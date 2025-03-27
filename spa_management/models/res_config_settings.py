# -*- coding: utf-8 -*-
###################################################################################

###################################################################################

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def booking_chairs(self):
        """
        return active chairs for booking
        """
        return self.env['spa.chair'].search(
            [('active_booking_chairs', '=', True)])

    @api.model
    def holidays(self):
        """
        return holiday
        """
        return self.env['spa.holiday'].search([('holiday', '=', True)])

    spa_booking_chair_ids = fields.Many2many(
        'spa.chair', string="Booking Chairs", default=booking_chairs)
    spa_holiday_ids = fields.Many2many('spa.holiday', string="Holidays",
                                         default=holidays)

    def execute(self):
        """
        update boolean fields of holiday and chair
        """
        spa_chair_obj = self.env['spa.chair'].search([])
        book_chair = []
        for chairs in self.spa_booking_chair_ids:
            book_chair.append(chairs.id)
        for records in spa_chair_obj:
            if records.id in book_chair:
                records.active_booking_chairs = True
            else:
                records.active_booking_chairs = False
        spa_holiday_obj = self.env['spa.holiday'].search([])
        holiday = []
        for days in self.spa_holiday_ids:
            holiday.append(days.id)
        for records in spa_holiday_obj:
            if records.id in holiday:
                records.holiday = True
            else:
                records.holiday = False
        #Modified by thanhtd for overriding ResConfigSettings
        return super(ResConfigSettings, self).execute()


class SpaWorkingHours(models.Model):
    _name = 'spa.working.hours'
    _description = 'Spa Working Hours'

    name = fields.Char(string="Working time")
    from_time = fields.Float(string="Start Time")
    to_time = fields.Float(string="End Time")


class SpaHoliday(models.Model):
    _name = 'spa.holiday'
    _description = 'Spa Holiday'

    name = fields.Char(string="Name")
    holiday = fields.Boolean(string="Holiday")
