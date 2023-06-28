from odoo import models, api, fields


class PayslipOverTime(models.Model):
    _inherit = 'hr.payslip'

    overtime_ids = fields.Many2many('hr.overtime')

    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    def _compute_input_line_ids(self):
        res = super()._compute_input_line_ids()
        vals = []
        for slip in self:
            overtime_type = self.env.ref('ohrms_overtime.hr_salary_rule_overtime')
            input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'OVERTIME')])
            contract = slip.contract_id
            input_line_overtime = slip.input_line_ids.filtered(lambda x: x.input_type_id.id == input_type.id)
            overtime_id = self.env['hr.overtime'].search([('employee_id', '=', slip.employee_id.id),
                                                          ('contract_id', '=', slip.contract_id.id),
                                                          ('state', '=', 'approved'),
                                                          ('date_from', '>=', slip.date_from),
                                                          ('date_to', '<=', slip.date_to),
                                                          ('payslip_paid', '=', False)])

            sum_overtime = sum(overtime_id.mapped('ot_payment_new'))
            overtime_id.write({'payslip_paid': True})
            if input_line_overtime:
                input_line_overtime.amount = sum_overtime
            else:
                if overtime_id:
                    slip.overtime_ids = overtime_id
                    input_data = {
                        'input_type_id': input_type.id,
                        'name': overtime_type.name,
                        'code': overtime_type.code,
                        'amount': sum_overtime,
                        'contract_id': contract.id,
                        'payslip_id':slip.id,
                    }
                    vals.append((0, 0, input_data))
                slip.update({'input_line_ids': vals})
        return res

    def action_payslip_done(self):
        """
        function used for marking paid overtime
        request.
        """
        for recd in self.overtime_ids:
            recd.payslip_paid = True
        return super(PayslipOverTime, self).action_payslip_done()
