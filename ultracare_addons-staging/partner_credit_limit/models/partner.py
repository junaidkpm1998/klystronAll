# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_remaining_credit(self):
        for i in self:
            moveline_obj = self.env['account.move.line']
            sale_obj = self.env['sale.order']
            movelines = moveline_obj.search(
                [('partner_id', '=', i.id),
                 ('move_id.move_type', 'in', ['out_invoice']),

                 # ('account_id.user_type_id.name', 'in',
                 #  ['Receivable', 'Payable']),
                 ('parent_state', '!=', 'cancel')]
            )
            confirm_sale_order = sale_obj.search(
                [('partner_id', '=', i.id),
                 ('state', '=', 'sale'),
                 ('invoice_status', '!=', 'invoiced')])
            debit, credit = 0.0, 0.0
            amount_total = 0.0
            for status in confirm_sale_order:
                amount_total += status.amount_total
            for line in movelines:
                credit += line.credit
                debit += line.debit
            partner_credit_limit = (debit + amount_total) - credit
            available_credit_limit = round(
                i.credit_limit - partner_credit_limit, 2)
            i.remaining_credit = available_credit_limit

    over_credit = fields.Boolean('Allow Over Credit?')
    warning_limit = fields.Float(compute='calculate_amount')
    remaining_credit = fields.Float(compute='get_remaining_credit')
    days_date = fields.Date()
    warning_percentage = fields.Integer(string="Warning Percentage", default=80)
    user_group_check = fields.Boolean(string="User Group field", compute='get_user', copy=False)
    vendor_credit_limit = fields.Float(
        string='Vendor Credit Limit', help='Vendor Credit limit specific to this partner.',
        groups='base.group_user',
        company_dependent=True, copy=False, readonly=False)
    credit_limit = fields.Float(
        string='Credit Limit', help='Credit limit specific to this partner.',
        groups='account.group_account_invoice,account.group_account_readonly',
        company_dependent=True, copy=False, readonly=False)
    use_partner_credit_limit = fields.Boolean(
        string='Partner Limit', groups='account.group_account_invoice,account.group_account_readonly', store=True)
    show_credit_limit = fields.Boolean(
        default=lambda self: self.env.company.account_use_credit_limit,
        compute='_compute_show_credit_limit', groups='account.group_account_invoice,account.group_account_readonly')
    check_credit_kg = fields.Boolean('Check Credit Bool', compute="onchange_partner_credit_limit_use")

    # credit_limit = fields.Float(
    #     string='Credit Limit', help='Credit limit specific to this partner.',
    #     company_dependent=True, copy=False)
    # use_partner_credit_limit = fields.Boolean(
    #     string='Partner Limit',
    #     compute='_compute_use_partner_credit_limit', inverse='_inverse_use_partner_credit_limit')

    @api.depends_context('company')
    def _compute_show_credit_limit(self):
        for partner in self:
            print("************", self.env.company.account_use_credit_limit)
            partner.show_credit_limit = self.env.company.account_use_credit_limit

    def get_user(self):
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        partner_group = res_user.has_group('sales_team.group_sale_salesman') and not res_user.has_group(
            'sales_team.group_sale_manager') and not res_user.has_group(
            'sales_team.group_sale_manager')
        if partner_group:
            self.user_group_check = True
        else:
            self.user_group_check = False

    @api.depends('credit_limit', 'warning_percentage')
    def calculate_amount(self):
        for i in self:
            limit = i.credit_limit
            percentage = i.warning_percentage
            total = (limit * percentage) / 100
            i.warning_limit = total

    @api.model
    @api.onchange('use_partner_credit_limit')
    @api.depends('check_credit_kg')
    def onchange_partner_credit_limit_use(self):
        if not self.use_partner_credit_limit:
            #     print("QQQQ", self.env['ir.property']._get('credit_limit', 'res.partner'), self.credit_limit)
            #     # self.credit_limit = self.env['ir.property']._get('credit_limit', 'res.partner')
            #     if self.credit_limit != self.env['ir.property']._get('credit_limit', 'res.partner'):
            #         print("keriiiiiii", self.env['ir.property']._get('credit_limit', 'res.partner'), self.credit_limit)
            #         self.credit_limit = self.env['ir.property']._get('credit_limit', 'res.partner')
            #     else:
            #         self.credit_limit = 0
            #     # self.credit_limit = 0
            #     self.check_credit_kg = False
            # else:
            if self.credit_limit == self.env['ir.property']._get('credit_limit', 'res.partner'):
                print("//////")
                self.write({'credit_limit': 0})
            else:
                self.credit_limit = 0
        else:
            print("keriiiiiii", self.env['ir.property']._get('credit_limit', 'res.partner'), self.credit_limit)
            if self.credit_limit != self.env['ir.property']._get('credit_limit',
                                                                 'res.partner') and self.credit_limit > 0:
                print("ITHA")
                self.credit_limit = self.credit_limit
            else:
                self.credit_limit = self.env['ir.property']._get('credit_limit', 'res.partner')
        self.check_credit_kg = True

    @api.depends_context('company')
    def _compute_use_partner_credit_limit(self):
        for partner in self:
            company_limit = self.env['ir.property']._get('credit_limit', 'res.partner')
            print("QWERTYUI")
            print("--->", partner.credit_limit, company_limit)
            partner.use_partner_credit_limit = partner.credit_limit != company_limit

    def _inverse_use_partner_credit_limit(self):
        for partner in self:
            if not partner.use_partner_credit_limit:
                partner.credit_limit = 0

    _sql_constraints = [
        ('partner_email_ult_uniq', 'unique (email)',
         'The Email of the customer/vendor must be unique per company !'),
        ('partner_name_ult_uniq', 'unique (name)',
         'The Name of the customer/vendor must be unique per company !')
    ]
