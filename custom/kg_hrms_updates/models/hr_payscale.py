from odoo import models, fields


class HrSalaryRule(models.Model):
    _name = 'hr.payscale'

    job_id = fields.Many2one('hr.job')
    type = fields.Many2one('hr.salary.rule', required=True)
    amount = fields.Integer(required=True)

    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Company', required=True, readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
