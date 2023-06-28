from odoo import models, api, fields


class PayslipHR(models.Model):
    _inherit = 'hr.payslip'

    leave_salary_ids = fields.Many2many('leave.salary.form')

    # @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    # def _compute_input_line_ids(self):
    #     res = super()._compute_input_line_ids()
    #     vals = []
    #     for slip in self:
    #         leave_salary_type = self.env.ref('kg_ultracare_hrms.hr_salary_rule_basic_salary')
    #         input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LEAVE-SALARY')])
    #         contract = slip.contract_id
    #         input_line_leave_salary = slip.input_line_ids.filtered(lambda x: x.input_type_id.id == input_type.id)
    #         leave_salary_id = self.env['leave.salary.form'].search([('employee_id', '=', self.employee_id.id),
    #                                                                 ('contract_id', '=', self.contract_id.id),
    #                                                                 ('state', '=', 'approved'),
    #                                                                 ('start_date', '>=', self.date_from),
    #                                                                 ('end_date', '<=', self.date_to),
    #                                                                 ('salary_structure', '=', self.struct_id.id),
    #                                                                 ('payslip_paid', '=', False)])
    #
    #         sum_leave_salary = sum(leave_salary_id.mapped('amount'))
    #         if input_line_leave_salary:
    #             input_line_leave_salary.amount = sum_leave_salary
    #         else:
    #             if leave_salary_id:
    #                 slip.leave_salary_ids = leave_salary_id
    #                 input_data = {
    #                     'input_type_id': input_type.id,
    #                     'name': leave_salary_type.name,
    #                     'code': leave_salary_type.code,
    #                     'amount': sum_leave_salary,
    #                     'contract_id': contract.id,
    #                 }
    #                 vals.append((0, 0, input_data))
    #             slip.update({'input_line_ids': vals})
    #     return res

    def action_payslip_done(self):
        """
        function used for marking paid overtime
        request.
        """
        for recd in self.leave_salary_ids:
            recd.payslip_paid = True
        return super(PayslipHR, self).action_payslip_done()
