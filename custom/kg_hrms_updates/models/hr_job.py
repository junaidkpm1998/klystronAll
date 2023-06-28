from odoo import models, fields


class HrJob(models.Model):
    _inherit = 'hr.job'

    interview_form_id = fields.Many2one('interview.form')
    pas_scale_ids = fields.One2many('hr.payscale', 'job_id')

