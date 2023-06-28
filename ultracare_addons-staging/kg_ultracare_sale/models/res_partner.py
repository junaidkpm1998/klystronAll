from odoo import models, fields, api
from odoo.exceptions import UserError


class PartnerCRM(models.Model):
    _inherit = 'res.partner'

    _rec_names_search = ['display_name', 'email', 'ref', 'vat',
                         'company_registry', 'temporary_sequence',
                         'customer_code']  # TODO vat must be sanitized the same way for storing/searching

    is_customer = fields.Boolean('Customer', default=False)
    temporary_sequence = fields.Char('Temporary ID', default="NEW")
    customer_code = fields.Char('Customer Code')
    total_due = fields.Monetary(
        compute='_compute_total_due',
        groups='account.group_account_readonly,account.group_account_invoice,sales_team.group_sale_salesman')

    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company')], default='company',
                                    compute='_compute_company_type', inverse='_write_company_type')
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')


    def _compute_total_due(self):
        today = fields.Date.context_today(self)
        for partner in self:
            total_overdue = 0
            total_due = 0
            for aml in partner.sudo().unreconciled_aml_ids:
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                if aml.company_id == self.env.company and not aml.blocked:
                    total_due += aml.amount_residual
                    if is_overdue:
                        total_overdue += aml.amount_residual
            partner.total_due = total_due
            partner.total_overdue = total_overdue

    @api.model
    def create(self, vals):
        vals['temporary_sequence'] = self.env['ir.sequence'].next_by_code('temporary.sequence')
        res = super(PartnerCRM, self).create(vals)
        return res

    # @api.constrains('state_id', 'country_id')
    # def _constrains_state(self):
    #     for rec in self:
    #         # if not rec.state_id:
    #         #     raise UserError("The operation cannot be completed: Contacts require a State")
    #         if not rec.country_id:
    #             raise UserError("The operation cannot be completed: Contacts require a Country")
