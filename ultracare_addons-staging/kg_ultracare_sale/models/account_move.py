import pytz
from num2words import num2words

from odoo import models, fields, api
from collections import defaultdict
from odoo.tools import float_compare, float_is_zero, formatLang


class AccountMoveSale(models.Model):
    _inherit = 'account.move'

    sale_location = fields.Many2one('sale.location', 'Sale Location')
    destination_location = fields.Many2one('sale.destination.location', 'Destination Location')
    description = fields.Selection([('description', 'Description'),
                                    ('alternate_des', 'Alternate Description'),
                                    ('invoice_des', 'Invoice Description')],
                                   string="Description", default='description')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    sale_order_customer_id = fields.Many2one('res.partner', string="Sale Order Customer",
                                             store=True)

    amount_in_words = fields.Char(required=False, compute="_amount_in_word", store=True)
    tax_amount_in_words = fields.Char(required=False, compute="_amount_in_word", store=True)
    po_no = fields.Char(string="PO reference")


    @api.depends('amount_total','amount_tax')
    def _amount_in_word(self):
        for rec in self:
            rec.amount_in_words = str(rec.currency_id.amount_to_text(rec.amount_total)).upper()
            rec.tax_amount_in_words = str(rec.currency_id.amount_to_text(rec.amount_tax)).upper()

    def _get_invoiced_lot_values_by_product(self, product_id):
        """ Get and prepare data to show a table of invoiced lot on the invoice's report. """
        self.ensure_one()
        user_tz = self.env.context.get('tz')
        res = []
        if self.state == 'draft' or not self.invoice_date or self.move_type not in ('out_invoice', 'out_refund'):
            return res

        current_invoice_amls = self.invoice_line_ids.filtered(
            lambda aml: not aml.display_type and aml.product_id and aml.quantity)
        all_invoices_amls = current_invoice_amls.sale_line_ids.invoice_lines.filtered(
            lambda aml: aml.move_id.state == 'posted').sorted(lambda aml: (aml.date, aml.move_name, aml.id))
        index = all_invoices_amls.ids.index(current_invoice_amls[:1].id) if current_invoice_amls[
                                                                            :1] in all_invoices_amls else 0
        previous_amls = all_invoices_amls[:index]

        previous_qties_invoiced = previous_amls._get_invoiced_qty_per_product()
        invoiced_qties = current_invoice_amls._get_invoiced_qty_per_product()
        invoiced_products = invoiced_qties.keys()

        qties_per_lot = defaultdict(float)
        previous_qties_delivered = defaultdict(float)
        stock_move_lines = current_invoice_amls.sale_line_ids.move_ids.move_line_ids.filtered(
            lambda sml: sml.state == 'done' and sml.lot_id).sorted(lambda sml: (sml.date, sml.id))
        for sml in stock_move_lines:
            if sml.product_id not in invoiced_products:
                continue
            product = sml.product_id
            product_uom = product.uom_id
            qty_done = sml.product_uom_id._compute_quantity(sml.qty_done, product_uom)

            if sml.location_id.usage == 'customer':
                # Cha Change 12/10/2022
                returned_qty = min(qties_per_lot[sml.lot_id, sml.location_id.id], qty_done)
                qties_per_lot[sml.lot_id, sml.location_id.id] -= returned_qty
                qty_done = returned_qty - qty_done

            previous_qty_invoiced = previous_qties_invoiced[product]
            previous_qty_delivered = previous_qties_delivered[product]
            # If we return more than currently delivered (i.e., qty_done < 0), we remove the surplus
            # from the previously delivered (and qty_done becomes zero). If it's a delivery, we first
            # try to reach the previous_qty_invoiced
            if float_compare(qty_done, 0, precision_rounding=product_uom.rounding) < 0 or \
                    float_compare(previous_qty_delivered, previous_qty_invoiced,
                                  precision_rounding=product_uom.rounding) < 0:
                previously_done = qty_done if sml.location_id.usage == 'customer' else min(
                    previous_qty_invoiced - previous_qty_delivered, qty_done)
                previous_qties_delivered[product] += previously_done
                qty_done -= previously_done
            # Cha Change 12/10/2022
            qties_per_lot[sml.lot_id, sml.location_id.id] += qty_done

        # Cha Change 12/10/2022
        for lot_location, qty in qties_per_lot.items():
            # Cha Change 12/10/2022
            lot, location_id = lot_location
            if lot.product_id.id == product_id:
                # access the lot as a superuser in order to avoid an error
                # when a user prints an invoice without having the stock access
                lot = lot.sudo()
                if float_is_zero(invoiced_qties[lot.product_id], precision_rounding=lot.product_uom_id.rounding) \
                        or float_compare(qty, 0, precision_rounding=lot.product_uom_id.rounding) <= 0:
                    continue
                invoiced_lot_qty = min(qty, invoiced_qties[lot.product_id])
                invoiced_qties[lot.product_id] -= invoiced_lot_qty
                expiry_date = False
                if lot.expiration_date:
                    expiry_date = pytz.UTC.localize(lot.expiration_date)
                    expiry_date = expiry_date.astimezone(pytz.timezone(user_tz))

                res.append({
                    'product_name': lot.product_id.display_name,
                    'quantity': formatLang(self.env, invoiced_lot_qty, dp='Product Unit of Measure'),
                    'uom_name': lot.product_uom_id.name,
                    'lot_name': lot.name,
                    'expiry': expiry_date.strftime("%d/%m/%Y, %H:%M:%S") if lot.expiration_date else False,
                    # The lot id is needed by localizations to inherit the method and add custom fields on the invoice's report.
                    'lot_id': lot.id,
                    'product_id': lot.product_id.id,
                    # Cha Change 12/10/2022
                    'location_id': location_id,
                })

        return res

    def get_line_items(self):
        for data in self:
            tabData = []
            lines = []
            length = len(data.invoice_line_ids)
            list_count = 0
            last = False
            last_lines = 0
            doc = {}
            for index, i in enumerate(range(0, length, 18), start=1):
                list_count = index
                lines.append(data.invoice_line_ids[i:i + 18])
            for index, line in enumerate(lines, start=1):
                if list_count == index:
                    last = True
                    last_lines = len(line)
                doc = {
                    'last_lines': last_lines,
                    'last': last,
                    'lines': line,
                }
                tabData.append(doc)
            return tabData


class AccountMoveLineDescription(models.Model):
    _inherit = "account.move.line"

    alternate_description = fields.Text('Alternate Description')
    invoice_description = fields.Text('Invoice Description')
    product_packaging_qty = fields.Float('Qty', default=1)
    package_id = fields.Many2one('product.packaging')
    pkg_unit_price = fields.Float()
    tax_amount = fields.Float(string="Tax Amount")
    tax_value = fields.Float(string="Tax Value")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_packaging_qty = 1.0

    @api.onchange('package_id', 'product_packaging_qty')
    def _onchange_product_packaging_id(self):
        if self.package_id:
            self.quantity = self.package_id.qty * self.product_packaging_qty

    @api.onchange('product_id')
    def _onchange_description(self):
        for line in self:
            if line.product_id:
                line.alternate_description = line.product_id.alternate_description
                line.invoice_description = line.product_id.invoice_description

    @api.onchange('tax_ids', 'price_subtotal')
    def _onchange_tax_value(self):
        x = []
        for rec in self:
            if rec.tax_ids:
                for i in rec.tax_ids:
                    value = ((i.amount) * (rec.price_subtotal)) / 100
                    x.append(value)
            tax_value = sum(x)
            rec.tax_value = tax_value
            rec.tax_amount = rec.price_subtotal + rec.tax_value
