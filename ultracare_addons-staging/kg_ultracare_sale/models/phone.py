from odoo import fields, models, api
from odoo.osv import expression


class PhoneMixin(models.AbstractModel):
    _inherit = 'mail.thread.phone'

    phone_mobile_search = fields.Char("Phone/Mobile", store=False, search='_search_phone_mobile_search')

    def _search_phone_mobile_search(self, operator, value):
        return [(0, '=', 1)]




