from odoo import api, fields, models


class PartnerModelInherit(models.Model):
    _inherit = 'res.partner'

    customer_type = fields.Selection([
        ('pre_paid', 'Pre Paid'),
        ('post_paid', 'Post Paid')
    ], 'Customer Type', required=True)

    # is_predefined_representatives = fields.Boolean(string="Is Predefined Representatives")
    predefined_representative_id = fields.Many2one('res.partner', string="Predefined Representative")
    journal_id = fields.Many2one('account.journal', string="Journal")
