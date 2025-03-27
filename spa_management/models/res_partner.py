# -*- coding: utf-8 -*-
###################################################################################

###################################################################################
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    partner_spa = fields.Boolean(string="Is a Spa Partner")
    # Added by huyendm for booking history
    # Corrected by thanhtd for showing the booking history data of this customer
    spa_booking_ids = fields.One2many(
        'spa.booking','customer_id', string='bookings')
    # End by thanhtd
    # End by huyendm 

    # delete partner when partner has not been booked or is an employee but has not been booked
    def unlink(self):
        ret = False        
        for rec in self:                
            if rec.id:                  
                sql_employee = "select count(*) from spa_booking_calendar_res_partner_rel where res_partner_id =" + str(rec.id)               
                rec.env.cr.execute(sql_employee)                
                employee = rec.env.cr.fetchall()[0] 

                sql_customer = "select count (*) from spa_booking where customer_id =" +str(rec.id)
                rec.env.cr.execute(sql_customer)
                customer = rec.env.cr.fetchall()[0]

                # do not delete if the number of selected partners > 1 and has been booked
                if len(self) > 1 and customer[0] > 0:
                    continue

                # do not delete if the number of selected partners > 1 and is the staff has been booked
                elif len(self) > 1 and employee[0] > 0:
                    continue

                # do not delete if the number of selected partner = 1 and has been booked
                elif len(self) == 1 and customer[0] > 0:                    
                    raise UserError(_("Delete failed because the partner is referenced by Spa's booking.\nReferencing table: spa_booking")) 
                 
                # do not delete if the number of selected partner = 1 and is the staff has been booked
                elif len(self) == 1 and employee[0] > 0:                           
                    raise UserError(_("Delete failed because the partner is referenced by Employee.\nReferencing table: spa_booking"))                  
                else:
                    ret = super(Partner, rec).unlink() 
        return ret   