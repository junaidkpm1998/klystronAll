from odoo import models, fields, _, api
from datetime import date
from odoo.exceptions import ValidationError, UserError


class HRLeave(models.Model):
    _inherit = 'hr.leave'

    deduct_from_annual_leave = fields.Boolean('Deduct from annual leave', required=True, default=False)

    @api.onchange('holiday_status_id')
    def _onchange_deduct_annual_leave(self):
        labours = self.employee_ids.filtered(lambda x:x.staff_type == 'labour')
        if self.holiday_status_id.deduct_from_annual_leave == True and len(labours) > 0:
            self.deduct_from_annual_leave = True
        if self.holiday_status_id.deduct_from_annual_leave == False:
            self.deduct_from_annual_leave = False

    def action_approve(self):
        """Sick leave is not allowed during probation period"""

        if self.holiday_status_id.restrict_on_probation:
            employee_count = len(self.employee_ids)
            vals = []
            dis_vals = []
            for i in self.employee_ids:
                if i.probation_completion_date < date.today():
                    vals.append(i.name)
                else:
                    dis_vals.append(i.name)
            if employee_count == len(vals):
                super(HRLeave, self).action_approve()
            else:
                listToStr = ','.join([str(elem) for elem in dis_vals])
                raise UserError(_("The Probation period of %s is not completed", listToStr))

        """Compensatory leave option will be there for office staff"""

        staff_employees = []
        if self.holiday_status_id.compensatory_leave == True:
            emp = 0
            for j in self.employee_ids:
                if j.staff_type != 'office_staff':
                    emp += 1
                    staff_employees.append(j.name)
                    listToStr = ','.join([str(elem) for elem in staff_employees])
            if emp > 0:
                raise ValidationError(_('Sorry %s is not Office Staff', listToStr))
            super(HRLeave, self).action_approve()

        """ Once enabled and confirm for labour deduct the number of leaves from annual leave allocation"""

        labour_employees = []
        if self.deduct_from_annual_leave == True:
            emp = 0
            for j in self.employee_ids:
                if j.staff_type != 'labour':
                    emp += 1
                    labour_employees.append(j.name)
                    listToStr = ','.join([str(elem) for elem in labour_employees])
            if emp > 0:
                raise ValidationError(_('Sorry %s is not labour staff', listToStr))
            super(HRLeave, self).action_approve()
        else:
            super(HRLeave, self).action_approve()

    def action_validate(self):
        """Create new negative annual allocation"""

        res = super(HRLeave, self).action_validate()
        if self.deduct_from_annual_leave == True:
            for j in self.employee_ids:
                employee_allocation = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', j.id), ('annual_leave_allocation', '=', True),
                     ('create_allocation', '=', False)], limit=1, order='id desc')
                print('1111',employee_allocation)
                for new_allocation in employee_allocation:
                    allocation = self.env['hr.leave.allocation'].create({
                        'name': 'Deduct Annual Leave Allocation for unpaid leave taken on %s' % (
                            self.request_date_from),
                        'holiday_status_id': new_allocation.holiday_status_id.id,
                        'date_from': new_allocation.date_from,
                        'allocation_type': 'regular',
                        'employee_id': new_allocation.employee_id.id,
                        'create_allocation': True,
                        'number_of_days': -self.number_of_days_display
                    })
                    allocation.action_confirm()
                    allocation.action_validate()
        return res


class HRLeavetype(models.Model):
    _inherit = 'hr.leave.type'

    restrict_on_probation = fields.Boolean('Restrict On Probation', default=False)
    deduct_from_annual_leave = fields.Boolean('Deduct from annual leave', default=False,
                                              help='If this field is True, a new negative record will be created from annual leave')
    annual_leave = fields.Boolean('Annual Leave', default=False)
    compensatory_leave = fields.Boolean('Compensatory Leave', default=False)


class HRAnnualAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    annual_leave_allocation = fields.Boolean('Annual Leave Allocation', related='holiday_status_id.annual_leave')
    create_allocation = fields.Boolean('Create Allocation', default=False, store=True)

    # Inheritrd to create negative leave record

    _sql_constraints = [
        ('duration_check',
         "CHECK(1=1)",
         "The duration must be greater than 0."),
    ]
