from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, html_keep_url, is_html_empty

from odoo.addons.payment import utils as payment_utils


@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()


class SaleModelInherit(models.Model):
    _inherit = 'sale.order'

    lang = fields.Selection(_lang_get, string='Language')
    sale_type = fields.Selection([('b2b', 'B2B'), ('b2c', 'B2C')], string='Sale Type', copy=True, index=True,
                                 tracking=3, default='b2b')

    b2c_type = fields.Selection([('normal', 'Normal'), ('white_label', 'White Label'), ('e_wallet', 'E Wallet(APP) '),
                                 ('group_gift', 'Group Gift(APP)')], string='B2C Sub Type', copy=True, index=True,
                                tracking=3,
                                help="Normal - Website portal,\nWhite Label - Purchase from some outlet, but payment will be received to YGG\n"
                                     "E Wallet (APP)- Happy credit, customer will buy some credit and keep it to purchase some coupons for later stage\n"
                                     "Group Gift (APP) - Customer will create a close group and each customer will contribute some money to purchase coupon")

    corporate_category = fields.Many2one('corporate.category', 'Corporate Category')
    partner_currency_id = fields.Many2one('res.currency', related='partner_id.currency_id', string='Partner Currency')

    @api.depends('sale_type')
    def onchange_sale_type(self):
        for data in self:
            data.b2c_type = False
            data.corporate_category = False

    def print_sale_report(self):
        self.message_post(body='Report Printed Successfully ')
        return self.env.ref('kg_ygg_sales.action_report_ygg_quotation').report_action(self, data=None)

    def kg_action_convert_invoice(self):
        for li in self.env['sale.order'].browse(self._context.get('active_ids')):
            lines = []
            for i in li.order_line:
                vals = {'product_id': i.product_id.id,
                        'quantity': 1,
                        'price_unit': i.price_unit,
                        'tax_ids': False,
                        'currency_id': li.currency_id.id}
                lines.append((0, 0, vals))
                

            return {'name': _('Convert Invoice'),
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    'context': {'default_partner_id': li.partner_id.id,
                                'default_invoice_date': li.date_order,
                                'default_payment_reference': li.name,
                                'default_move_type': 'out_invoice',
                                'default_invoice_line_ids': lines,
                                },
                    'type': 'ir.actions.act_window', }


class KgSaleOrder(models.Model):
    _name = 'kg.sale.order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Kg Sales Order"
    _order = 'date_order desc, id desc'
    _check_company_auto = True

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    reference = fields.Char(string='Payment Ref.', copy=False,
                            help='The payment communication of this sale order.')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False)]}, copy=False,
                                 default=fields.Datetime.now,
                                 help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    validity_date = fields.Date(string='Expiration', readonly=True, copy=False,
                                states={'draft': [('readonly', False)]}, )

    user_id = fields.Many2one(
        'res.users', string='Salesperson', index=True, tracking=2, default=lambda self: self.env.user,
        domain=lambda self: "[('groups_id', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
            self.env.ref("sales_team.group_sale_salesman").id))
    order_line = fields.One2many('kg.sale.order.line', 'order_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
                                 auto_join=True)
    note = fields.Html('Terms and conditions')
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    total_amount = fields.Float('Total', compute='_compute_total')
    sale_type = fields.Selection([('b2b', 'B2B'), ('b2c', 'B2C')], string='Sale Type', copy=True, index=True,
                                 tracking=3, default='b2b')

    b2c_type = fields.Selection([('normal', 'Normal'), ('white_label', 'White Label'), ('e_wallet', 'E Wallet(APP) '),
                                 ('group_gift', 'Group Gift(APP)')], string='B2C Type', copy=True, index=True,
                                tracking=3,
                                help="Normal - Website portal,\nWhite Label - Purchase from some outlet, but payment will be received to YGG\n"
                                     "E Wallet (APP)- Happy credit, customer will buy some credit and keep it to purchase some coupons for later stage\n"
                                     "Group Gift (APP) - Customer will create a close group and each customer will contribute some money to purchase coupon")

    corporate_category = fields.Many2one('corporate.category', 'Corporate Category')

    @api.depends('sale_type')
    def onchange_sale_type(self):
        for data in self:
            data.b2c_type = False
            data.corporate_category = False

    @api.depends('order_line')
    def _compute_total(self):
        total_amount = 0
        for data in self.order_line:
            total_amount += data.price_total
        self.total_amount = total_amount

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(
                    _('You can not delete a sent quotation or a confirmed sales order. You must first cancel it.'))

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('kg.sale.order', sequence_date=seq_date) or _('New')
        result = super(KgSaleOrder, self).create(vals)
        return result

    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel'])
        return orders.write({
            'state': 'draft',
        })

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_confirm(self):
        return self.write({'state': 'sale'})

    def action_done(self):
        return self.write({'state': 'done'})


class SaleOrderLine(models.Model):
    _name = 'kg.sale.order.line'
    _description = 'Kg Sales Order Line'

    order_id = fields.Many2one('kg.sale.order', string='Order Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    name = fields.Text(string='User Name', required=True)
    tax_id = fields.Many2many('account.tax', string='Taxes', context={'active_test': False})
    state = fields.Selection(related='order_id.state', string='Order Status', copy=False, store=True)
    price_unit = fields.Float('Unit Price', required=True, default=0.0)
    price_tax = fields.Float(string='Total Tax', store=True)
    price_total = fields.Float(tring='Total', store=True)
    user_id = fields.Integer('User Id')
    vendor_id = fields.Many2one('res.partner', string='Vendor', index=True, tracking=2)
    partner_id = fields.Many2one('res.partner', string='Company', required=True, change_default=True, index=True,
                                 tracking=1)
    currency_id = fields.Many2one('res.currency', store=True, ondelete="restrict",
                                  default=lambda self: self.env.company.currency_id)
    country_id = fields.Many2one('res.country', 'Country')
    maf = fields.Char('MAF #')
    activity = fields.Char('Activity Name')
    promotion_program = fields.Char('Promotion Program')
