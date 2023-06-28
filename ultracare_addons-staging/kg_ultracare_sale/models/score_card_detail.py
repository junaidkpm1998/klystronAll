from odoo import models, fields, api


class ScoreCardDetail(models.Model):
    _name = 'score.card.detail'

    crm_id = fields.Many2one('crm.lead', string="Opportunity", readonly=True)
    name = fields.Many2one(
        'crm.stage', string='Stage', index=True, readonly=True,
        domain="['|', ('team_id', '=', False), ('team_id', '=', team_id)]")
    date = fields.Date("Date")
    days = fields.Integer("Days")
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    lead_create_date = fields.Datetime(string="Lead Creation Date", readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    is_won = fields.Boolean(string='Is Won', related='crm_id.stage_id.is_won', store=True)
    is_lost = fields.Float(string='Is Lost', related='crm_id.probability', store=True)
    stage_id = fields.Many2one(
        'crm.stage', related='crm_id.stage_id', string="Current Stage", store=True)
    is_admin = fields.Boolean(string='Is Admin', default=False)

    @api.constrains('user_id')
    def _access_readonly(self):
        if self.env.user.has_group('base.group_erp_manager'):
            self.is_admin = True
