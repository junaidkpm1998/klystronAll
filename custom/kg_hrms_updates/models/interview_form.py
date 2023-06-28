from odoo import fields, models


class InterviewForm(models.Model):
    _name = 'interview.form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    interview_form = fields.Char()
