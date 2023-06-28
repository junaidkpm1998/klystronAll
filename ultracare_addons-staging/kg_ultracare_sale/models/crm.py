from odoo import models, fields, api

MENU_ITEM_SEPARATOR = "/"


class SubStageCRM(models.Model):
    _name = 'sub.crm'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='Sub-Stages Name')
    parent_pipeline = fields.Many2one('crm.stage', string='Parent Stages', required=1)
    is_won_substage = fields.Boolean(string='Is Won Stage?')
    folder_in_pipeline_substage = fields.Boolean(string='Folder in Pipeline?')
    requirements_substage = fields.Text('REQUIREMENTS',
                                        help="Enter here the internal requirements for this stage (ex: Offer sent to customer). It will appear as a tooltip over the stage's name.")
    full_stage = fields.Char('Sub Stages')
    default_substage = fields.Boolean('Default Substage', default=False)

    @api.model
    def create(self, vals):
        """Join substage and parent stage"""

        res = super(SubStageCRM, self).create(vals)
        full_stage_path = str(res.parent_pipeline.name) + '/' + str(res.name)
        res.full_stage = full_stage_path
        return res

    def write(self, values):
        if 'parent_pipeline' in values:
            name = values['name'] if 'name' in values else self.name
            full_stage_path = str(self.env['crm.stage'].browse(values['parent_pipeline']).name or '') + '/' + str(name)
            values['full_stage'] = full_stage_path
        return super(SubStageCRM, self).write(values)

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, "%s/ %s" % (rec.parent_pipeline.name, rec.name)))
        return res


class CRMLeadSubstage(models.Model):
    _inherit = 'crm.lead'

    closed_date_new = fields.Datetime('Closed Date', related='date_closed')
    substage = fields.Char('Substage')
    substage_id = fields.Many2one(
        comodel_name='sub.crm',
        string='Substage',
        required=False, tracking=True)
    lead_stage = fields.Many2one(related='stage_id')
    checklist_stage = fields.Many2many('crm.stage')
    checklist = fields.Html('Checklist', copy=False)
    is_lost = fields.Boolean(default=False, string='Is Lost')

    score_card_line_ids = fields.One2many('score.card.detail', 'crm_id', string="Score Card Details")

    def toggle_active(self):
        if self.is_lost:
            stage_id_sec = self.env['crm.stage'].search([], order='sequence asc')
            self.stage_id = stage_id_sec[0].id
            res = super(CRMLeadSubstage, self).toggle_active()
            restore_id = self.env.ref('kg_ultracare_sale.stage_lead_restore')
            score_obj = self.env['score.card.detail'].search([('crm_id', '=', self._origin.id)], limit=1,
                                                             order='id desc')
            restore_vals = []
            restore_data = {
                'name': restore_id.id,
                'crm_id': self.id if self.id else self._origin.id,
                'partner_id': self.partner_id.id,
                'lead_create_date': self.create_date,
                'user_id': self.user_id.id,
                'date': fields.date.today(),
                'days': (fields.date.today() - score_obj.date).days if score_obj.date else 0
            }
            restore_vals.append((0, 0, restore_data))
            self.update({'score_card_line_ids': restore_vals})

            new_vals = []
            stage_id = self.env['crm.stage'].search([], limit=1)
            new_data = {
                'name': stage_id.id,
                'crm_id': self.id if self.id else self._origin.id,
                'partner_id': self.partner_id.id,
                'lead_create_date': self.create_date,
                'user_id': self.user_id.id,
                'date': fields.date.today(),
                'days': (fields.date.today() - score_obj.date).days if score_obj.date else 0
            }
            new_vals.append((0, 0, new_data))
            self.write({'score_card_line_ids': new_vals})
            self.is_lost = False

            return res
        else:
            return super(CRMLeadSubstage, self).toggle_active()

    def action_set_won_rainbowman(self):
        res = super(CRMLeadSubstage, self).action_set_won_rainbowman()
        score_obj = self.env['score.card.detail'].search([('crm_id', '=', self._origin.id)], limit=1,
                                                         order='id desc')
        won_stages = self._stage_find(domain=[('is_won', '=', True)], limit=1)
        vals = []
        data = {
            'name': won_stages.id,
            'crm_id': self.id if self.id else self._origin.id,
            'partner_id': self.partner_id.id,
            'lead_create_date': self.create_date,
            'user_id': self.user_id.id,
            'date': fields.date.today(),
            'days': (fields.date.today() - score_obj.date).days if score_obj.date else 0
        }
        vals.append((0, 0, data))
        self.write({'score_card_line_ids': vals})
        return res

    @api.model
    def create(self, values):
        res = super(CRMLeadSubstage, self).create(values)
        if res.stage_id:
            checklist = res.stage_id.checklist or False
            res.checklist = checklist
            sub_stage = self.env['sub.crm'].search(
                [('parent_pipeline', '=', res.stage_id.id), ('default_substage', '=', True)], limit=1)
            res.substage_id = sub_stage.id
            res.checklist_stage = [(4, res.lead_stage.id)]
            score_obj = self.env['score.card.detail'].search([('crm_id', '=', res._origin.id)], limit=1,
                                                             order='id desc')
            self.env['score.card.detail'].create({
                'crm_id': res.id if res.id else res._origin.id,
                'name': res.stage_id.id,
                'partner_id': res.partner_id.id,
                'lead_create_date': res.create_date,
                'user_id': res.user_id.id,
                'date': fields.date.today(),
                'days': (fields.date.today() - score_obj.date).days if score_obj.date else 0
            })
        return res

    @api.onchange('stage_id')
    def _onchange_substage(self):
        for data in self:
            if data.lead_stage:
                substage_id = self.env['sub.crm'].search(
                    [('default_substage', '=', True), ('parent_pipeline', '=', data.lead_stage.id)])
                self.substage = substage_id.name
                self.substage_id = substage_id.id
            if data.stage_id:
                score_obj = self.env['score.card.detail'].search([('crm_id', '=', data._origin.id)], limit=1,
                                                                 order='id desc')
                self.env['score.card.detail'].create({
                    'crm_id': data.id if data.id else data._origin.id,
                    'name': data.stage_id.id,
                    'partner_id': data.partner_id.id,
                    'lead_create_date': data.create_date,
                    'user_id': data.user_id.id,
                    'date': fields.date.today(),
                    'days': (fields.date.today() - score_obj.date).days if score_obj.date else 0
                })

    @api.onchange('lead_stage')
    def _onchange_stage(self):
        for data in self:
            if data.lead_stage:
                data.checklist_stage = [(4, data.lead_stage.id)]

    @api.onchange('lead_stage')
    def _onchange_checklist(self):
        for rec in self:
            if rec.lead_stage.id not in rec.checklist_stage.ids:
                if rec.lead_stage.checklist:
                    if rec.checklist:
                        value = str(rec.checklist) + str(rec.lead_stage.checklist)
                    else:
                        value = str(rec.lead_stage.checklist)
                    rec.checklist = value


class CRMLeadChecklist(models.Model):
    _inherit = 'crm.stage'

    checklist = fields.Html('Checklist')
    active = fields.Boolean(default=True)


class KGCRMLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    kg_lead_id = fields.Many2one('crm.lead', string='Lead')

    def action_lost_reason_apply(self):
        res = super(KGCRMLost, self).action_lost_reason_apply()
        lost_id = self.env.ref('kg_ultracare_sale.stage_lead_lost')
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        leads.is_lost = True
        score_obj = self.env['score.card.detail'].search([('crm_id', '=', leads._origin.id)], limit=1,
                                                         order='id desc')
        vals = []
        data = {
            'crm_id': leads.id if leads.id else leads._origin.id,
            'name': lost_id.id,
            'partner_id': leads.partner_id.id,
            'lead_create_date': leads.create_date,
            'user_id': leads.user_id.id,
            'date': fields.date.today(),
            'days': (fields.date.today() - score_obj.date).days if score_obj.date else 0
        }
        vals.append((0, 0, data))
        leads.write({'score_card_line_ids': vals})

        return res
