from odoo import api, fields, models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    coupon_code = fields.Selection([('ygg','YGG Generated'),('api_code','API Code'),('present_code','Preset Code')],string='Coupon Code', copy=True,
                                   help="YGG - will be redemed from YGG portal by login,\nAPI code - can be redeemed from POS outlets.\n"
                                     "Preset code- Should have inventory in system\n")
    present_code_type = fields.Selection([('issurance','Issurance Basis'),('redemption','Redemption Basis'),('sold','Sold Basis')],string='Present Code Type', copy=True,
                                   help="Issurance Basis - Based on coupon purchased from vendor,\nRedumption basis - Pay based on customer redeem.\n"
                                     "Sold Basis - pay based on customer purchase coupon.\n")

    api_type = fields.Selection([('prepaid','Prepaid'),('postpaid','Post-paid')],string='Api Type', copy=True)

    @api.onchange('coupon_code')
    def onchange_coupon_code(self):
        for data in self:
            data.present_code_type = False
            data.api_type = False


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    coupon_code = fields.Selection([('ygg','YGG Generated'),('api_code','API Code'),('present_code','Preset Code')],string='Coupon Code', copy=True,
                                   help="YGG - will be redemed from YGG portal by login,\nAPI code - can be redeemed from POS outlets.\n"
                                     "Preset code- Should have inventory in system\n")
    present_code_type = fields.Selection([('issurance','Issurance Basis'),('redemption','Redemption Basis'),('sold','Sold Basis')],string='Present Code Type', copy=True,
                                   help="Issurance Basis - Based on coupon purchased from vendor,\nRedumption basis - Pay based on customer redeem.\n"
                                     "Sold Basis - pay based on customer purchase coupon.\n")

    api_type = fields.Selection([('prepaid','Prepaid'),('postpaid','Post-paid')],string='Api Type', copy=True)

    @api.onchange('coupon_code')
    def onchange_coupon_code(self):
        for data in self:
            data.present_code_type = False
            data.api_type = False