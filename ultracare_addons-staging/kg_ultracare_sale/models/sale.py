from datetime import date

from odoo import models, fields, api, _
from odoo.addons.sale.models.sale_order import READONLY_FIELD_STATES

LOCKED_FIELD_STATES = {
    state: [('readonly', True)]
    for state in {'done', 'cancel'}
}


class SaleOrderCRM(models.Model):
    _inherit = 'sale.order'
    _description = 'Sale Quotation'

    sale_location = fields.Many2one('sale.location', 'Sale Location', tracking=1)
    destination_location = fields.Many2one('sale.destination.location', 'Destination Location', tracking=1)
    description = fields.Selection([('description', 'Description'),
                                    ('alternate_des', 'Alternate Description')],
                                   string="Description", default='description', tracking=1)
    product_name = fields.Char(string='Product', readonly=True)
    onhand_qty = fields.Char(string='On Hand Quantity', readonly=True)
    reserved_qty = fields.Char(string='Reserved Quantity', readonly=True)
    last_selling_price = fields.Monetary(currency_field='currency_id', string='Last Selling Price', readonly=True)
    ordered_qty = fields.Float()

    amount_in_words = fields.Char(required=False, compute="_amount_in_word", store=True)
    tax_amount_in_words = fields.Char(required=False, compute="_amount_in_word", store=True)

    total_gross_weight = fields.Float(string="Total Weight", compute="_compute_volume_weight")
    total_gross_volume = fields.Float(string="Total Volume", compute="_compute_volume_weight")

    volume_uom_name = fields.Char(string='Volume unit of measure label', compute='_compute_volume__weight_uom_name',
                                  store=True)
    weight_uom_name = fields.Char(string='Weight unit of measure label', compute='_compute_volume__weight_uom_name',
                                  store=True)

    is_print = fields.Boolean(default=False)
    is_revised = fields.Boolean(default=True)
    po_reference = fields.Char(string="PO reference")

    # Tracking fields
    partner_invoice_id = fields.Many2one(
        comodel_name='res.partner',
        string="Invoice Address",
        compute='_compute_partner_invoice_id',
        store=True, readonly=False, required=True, precompute=True,
        states=LOCKED_FIELD_STATES,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1)

    partner_shipping_id = fields.Many2one(
        comodel_name='res.partner',
        string="Delivery Address",
        compute='_compute_partner_shipping_id',
        store=True, readonly=False, required=True, precompute=True,
        states=LOCKED_FIELD_STATES,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1)

    sale_order_template_id = fields.Many2one(
        comodel_name='sale.order.template',
        string="Quotation Template",
        compute='_compute_sale_order_template_id',
        store=True, readonly=False, check_company=True, precompute=True,
        states=READONLY_FIELD_STATES,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1)

    validity_date = fields.Date(
        string="Expiration",
        compute='_compute_validity_date',
        store=True, readonly=False, copy=False, precompute=True,
        states=READONLY_FIELD_STATES, tracking=1)

    date_order = fields.Datetime(
        string="Order Date",
        required=True, readonly=False, copy=False,
        states=READONLY_FIELD_STATES,
        help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.",
        default=fields.Datetime.now, tracking=1)

    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string="Payment Terms",
        compute='_compute_payment_term_id',
        store=True, readonly=False, precompute=True, check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1)

    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company, tracking=1)

    require_signature = fields.Boolean(
        string="Online Signature",
        compute='_compute_require_signature',
        store=True, readonly=False, precompute=True, tracking=1,
        states=READONLY_FIELD_STATES,
        help="Request a online signature and/or payment to the customer in order to confirm orders automatically.")

    require_payment = fields.Boolean(
        string="Online Payment",
        compute='_compute_require_payment', tracking=1,
        store=True, readonly=False, precompute=True,
        states=READONLY_FIELD_STATES)

    client_order_ref = fields.Char(string="Customer Reference", copy=False, tracking=1)

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string="Fiscal Position",
        compute='_compute_fiscal_position_id',
        store=True, readonly=False, precompute=True, check_company=True,
        help="Fiscal positions are used to adapt taxes and accounts for particular customers or sales orders/invoices."
             "The default value comes from the customer.",
        domain="[('company_id', '=', company_id)]", tracking=1)

    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string="Analytic Account",
        copy=False, check_company=True,  # Unrequired company
        states=READONLY_FIELD_STATES,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1)

    incoterm = fields.Many2one(
        'account.incoterms', 'Incoterm', tracking=1,
        help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")

    incoterm_location = fields.Char(string='Incoterm Location', tracking=1)

    picking_policy = fields.Selection([
        ('direct', 'As soon as possible'),
        ('one', 'When all products are ready')], tracking=1,
        string='Shipping Policy', required=True, readonly=True, default='direct',
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help="If you deliver all products at once, the delivery order will be scheduled based on the greatest "
             "product lead time. Otherwise, it will be based on the shortest.")

    commitment_date = fields.Datetime(
        string="Delivery Date", copy=False, tracking=1,
        states=LOCKED_FIELD_STATES,
        help="This is the delivery date promised to the customer. "
             "If set, the delivery order will be scheduled based on "
             "this date rather than product lead times.")

    origin = fields.Char(
        string="Source Document", tracking=1,
        help="Reference of the document that generated this sales order request")

    opportunity_id = fields.Many2one(
        'crm.lead', string='Opportunity', check_company=True, tracking=1,
        domain="[('type', '=', 'opportunity'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    campaign_id = fields.Many2one(ondelete='set null', tracking=1)
    medium_id = fields.Many2one(ondelete='set null', tracking=1)
    source_id = fields.Many2one(ondelete='set null', tracking=1)

    @api.depends('partner_id')
    def _compute_partner_shipping_id(self):
        for order in self:
            order.partner_shipping_id = order.partner_id.address_get(['delivery'])[
                'delivery'] if order.partner_id else False

    @api.depends('order_line')
    def _compute_volume__weight_uom_name(self):
        for rec in self:
            if rec.order_line:
                rec.volume_uom_name = rec.order_line[0].product_id.volume_uom_name
                rec.weight_uom_name = rec.order_line[0].product_id.weight_uom_name

    @api.depends('amount_total', 'amount_tax')
    def _amount_in_word(self):
        for res in self:
            for rec in res.currency_id:
                res.amount_in_words = str(rec.amount_to_text(res.amount_total)).upper()
                res.tax_amount_in_words = str(rec.amount_to_text(res.amount_tax)).upper()

    @api.depends('order_line')
    def _compute_volume_weight(self):
        weight = []
        volume = []
        for rec in self:
            for line in rec.order_line:
                weight.append(line.gross_weight_qty)
                volume.append(line.gross_volume_qty)
            rec.total_gross_volume = sum(volume)
            rec.total_gross_weight = sum(weight)

    def _find_mail_template(self):
        """ Get the appropriate mail template for the current sales order based on its state.

        If the SO is confirmed, we return the mail template for the sale confirmation.
        Otherwise, we return the quotation email template.

        :return: The correct mail template based on the current status
        :rtype: record of `mail.template` or `None` if not found
        """
        self.ensure_one()
        if self.env.context.get('proforma') or self.state not in ('sale', 'done'):
            return self.env.ref('kg_ultracare_sale.custom_proforma_email_template_sale', raise_if_not_found=False)
        else:
            return self._get_confirmation_template()

    def get_line_items(self):
        for data in self:
            tabData = []
            lines = []
            length = len(data.order_line)
            list_count = 0
            last = False
            last_lines = 0
            doc = {}
            for index, i in enumerate(range(0, length, 18), start=1):
                list_count = index
                lines.append(data.order_line[i:i + 18])
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

    def action_confirm(self):
        self.partner_id.is_customer = True
        if not self.partner_id.customer_code:
            partner = self.partner_id.name
            self.partner_id.customer_code = "C" + partner[0] + self.env['ir.sequence'].next_by_code(
                'customercode.sequence')

        for rec in self.order_line:
            if rec.sp_unit_amt:
                if rec.sp_unit_amt != rec.price_unit:
                    rec.price_unit = rec.sp_unit_amt
        self.message_post(body="Sale Order Created")
        res = super(SaleOrderCRM, self).action_confirm()
        for rec in self.picking_ids:
            rec.payment_term_id = self.payment_term_id.id
        return res


    def _prepare_invoice(self):
        res = super(SaleOrderCRM, self)._prepare_invoice()
        res.update({'sale_location': self.sale_location.id,
                    'destination_location': self.destination_location.id,
                    })
        return res


class SaleOrderLineDescription(models.Model):
    _inherit = "sale.order.line"

    alternate_description = fields.Text('Alternate Description')
    invoice_description = fields.Text('Invoice Description')
    tax_amount = fields.Float(string="Tax Amount")
    tax_value = fields.Float(string="Tax Value")
    gross_weight = fields.Float(string="Weight")
    gross_volume = fields.Float(string="Volume")
    gross_weight_qty = fields.Float(string="Weight Quantity", compute="_compute_gross_value")
    gross_volume_qty = fields.Float(string="Volume Quantity", compute="_compute_gross_value")

    check_user_group = fields.Boolean(string="check User Group", compute='compute_get_user', copy=False, store=True)

    @api.onchange('tax_id', 'price_subtotal')
    def _onchange_tax_value(self):
        x = []
        for rec in self:
            if rec.tax_id:
                for i in rec.tax_id:
                    value = ((i.amount) * (rec.price_subtotal)) / 100
                    x.append(value)
            tax_value = sum(x)
            rec.tax_value = tax_value
            rec.tax_amount = rec.price_subtotal + rec.tax_value

    @api.onchange('product_id')
    def _onchange_gross_weight(self):
        for rec in self:
            if rec.product_id:
                rec.gross_weight = rec.product_id.weight
                rec.gross_volume = rec.product_id.volume

    @api.depends('gross_weight', 'gross_volume', 'product_uom_qty')
    def _compute_gross_value(self):
        for rec in self:
            rec.gross_weight_qty = rec.gross_weight * rec.product_uom_qty
            rec.gross_volume_qty = rec.gross_volume * rec.product_uom_qty

    @api.depends('product_id')
    def compute_get_user(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        partner_group = res_user.has_group('stock.group_stock_user')
        if partner_group:
            self.check_user_group = True
        else:
            self.check_user_group = False

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLineDescription, self)._prepare_invoice_line(**optional_values)
        res.update({
            'alternate_description': self.alternate_description,
            'invoice_description': self.invoice_description,
        })
        return res

    def get_product_info(self):
        if str(self.id).isdecimal():
            order_line = self.env['sale.order.line'].browse(self.id)
            sale_order = order_line.order_id
            product = order_line.product_id
            sale_order.write({
                'product_name': order_line.name,
                'onhand_qty': product.qty_available,
                'reserved_qty': product.qty_available - product.virtual_available,
                'ordered_qty': order_line.product_uom_qty,
            })
            orders = self.env['sale.order'].search(
                [('partner_id', '=', sale_order.partner_id.id), ('state', 'in', ('sale', 'done')),
                 ('date_order', '<', sale_order.date_order)])
            order_lines = orders.order_line
            prev_product_line = order_lines.filtered(lambda line: line.product_id.id == product.id)
            if prev_product_line:
                sale_order.last_selling_price = prev_product_line[0].price_unit
            else:
                sale_order.last_selling_price = 0.00

    @api.onchange('product_id')
    def _onchange_description_product(self):
        for line in self:
            if line.product_id:
                line.alternate_description = line.product_id.alternate_description
                line.invoice_description = line.product_id.invoice_description


class SaleLocation(models.Model):
    _name = "sale.location"
    _description = 'Sale Location'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Text(string='Name', required=True, tracking=True)


class SaleDestLocation(models.Model):
    _name = "sale.destination.location"
    _description = 'Destination Location'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Text(string='Name', required=True, tracking=True)
