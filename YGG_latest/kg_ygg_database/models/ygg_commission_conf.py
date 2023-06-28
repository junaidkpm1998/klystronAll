from odoo import api, fields, models, _


class YggCommissionConf(models.Model):
    _name = 'ygg.commission.conf'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YGG Commission Conf'

    corporate_id = fields.Many2one('res.partner', string="Vendor")
    commission_type = fields.Selection(
        [('percentage', 'Percentage'), ('fixed', 'Fixed'), ('fixed_percentage', 'Fixed Percentage'),
         ('denomination', 'Denomination'), ('deduct_percentage', 'Deduct Amount & Percentage')])
    start_date = fields.Datetime("Start Date")
    end_date = fields.Datetime("End Date")
    currency_id = fields.Many2one('res.currency', string='Odoo Currency', default=lambda self: self.env.company.currency_id)
    sale_orders = fields.Many2many('sale.order', string="Sale Orders")
    commission_line_ids = fields.One2many('ygg.commission.line', 'commission_conf_id', string="Commission Line")


class YggCommissionLine(models.Model):
    _name = 'ygg.commission.line'

    commission_conf_id = fields.Many2one('ygg.commission.conf')
    brand_id = fields.Many2one('product.product')
    commission_amount = fields.Float('Commission Amount')
    commission_per = fields.Float('Commission %')
    product_qty = fields.Float('Product Qty')
    unit_price = fields.Float('Unit Price')
    sub_total = fields.Float('Sub Total')