# -*- coding: utf-8 -*-
###################################################################################

###################################################################################
import logging
from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
_logger = logging.getLogger(__name__)
class Users(models.Model):
    _inherit = 'res.users'

    # Chair user. not use now
    # user_spa_active = fields.Boolean(
    #     string="Active Spa Users", default=False)

# Add model for access right model hr.employee.public in file security/ir.model.access.csv
class HREmployeePublic(models.Model):
    _inherit = 'hr.employee.public'


class EmployeeInherit(models.Model):
    _inherit = 'hr.employee'
    # Delele employee
    # If the employee has been booked, it cannot be deleted
    # If the employee has not been booked, it will be deleted
    def unlink(self):
        res = False      
        for rec in self:                
            if rec.work_contact_id:
                sql = "select count(*) from spa_booking_calendar_res_partner_rel where res_partner_id =" + str(rec.work_contact_id.id)
                rec.env.cr.execute(sql)
                list_partner = rec.env.cr.fetchall()[0]  
                # do not delete if the number of employees is selected > 1 and the selected employees is already booked
                if len(self) > 1 and list_partner[0] != 0:
                    continue 
                # do not delete if number of selected staff = 1 and selected staff is already booked  
                elif len(self) == 1 and list_partner[0] != 0:
                    raise UserError(_("Delete failed because the staff is referenced by Spa's booking.\nReferencing table: spa_booking"))             
                else:
                    res = super(EmployeeInherit, rec).unlink()    
        return res       

# Add model for access right model hr.department in file security/ir.model.access.csv
class HRDepartment(models.Model):
    _inherit = 'hr.department'