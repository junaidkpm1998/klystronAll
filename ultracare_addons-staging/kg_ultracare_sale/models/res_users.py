from odoo import fields, models, api
from odoo.osv import expression


class ResUsersSaleManCode(models.Model):
    _inherit = "res.users"

    sale_man_code = fields.Char('Salesman Code')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        user_ids = []
        if operator not in expression.NEGATIVE_TERM_OPERATORS:
            if operator == 'ilike' and not (name or '').strip():
                domain = []
            else:
                domain = ['|', ('login', '=', name), ('sale_man_code', '=', name)]
            user_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        if not user_ids:
            user_ids = self._search(
                expression.AND([['|', ('name', operator, name), ('sale_man_code', operator, name)], args]), limit=limit,
                access_rights_uid=name_get_uid)
        return user_ids


class ResCompanyInheritBank(models.Model):
    _inherit = 'res.company'
    _description = 'Include custom Field'

    account_number = fields.Char(string='Account Number')
    bank = fields.Many2one('res.bank', string='Bank Name')
    branch = fields.Char(string='Branch')
    beneficiary = fields.Char(string='BENEFICIARY')
    iban_no = fields.Char(string='IBAN NO')
    swift_code = fields.Char(string='SWIFT CODE')

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     args = args or []
    #     print(args, "ARRRAAAAAAAAAA")
    #     domain = []
    #     if name:
    #         domain = ['|', ('sale_man_code', operator, name)]
    #     return super(ResCompanyInheritBank, self).name_search(name, args=args, operator=operator, limit=limit)


