# -*- coding: utf-8 -*-
###################################################################################

###################################################################################

from odoo import api, fields, models


class Contacts(models.Model):
    _name = 'spa.booking.filter'
    _description = 'Spa booking Filters'

    user_id = fields.Many2one('res.users', 'Me', required=True, default=lambda self: self.env.user, index=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    
    partner_id = fields.Many2one('res.partner', 'Employee', required=True, index=True, domain=lambda self:[('id', 'in', self.env['hr.employee'].search([]).work_contact_id.ids),('company_id','=',self.env.company.id)])
    active = fields.Boolean('Active', default=True)
    partner_checked = fields.Boolean('Checked', default=True)  # used to know if the partner is checked in the filter of the calendar view for the user_id.
    
    _sql_constraints = [
        ('user_id_partner_id_unique', 'UNIQUE(user_id, partner_id)', 'A user cannot have the same contact twice.')
    ]

    @api.model
    def unlink_from_partner_id(self, partner_id):
        return self.search([('partner_id', '=', partner_id)]).unlink()
       
