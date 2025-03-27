# -*- coding: utf-8 -*-
###################################################################################
#
#
###################################################################################

import json
import pytz,re
from datetime import datetime, time, timedelta

from odoo import fields, http, tools, _
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)
from pytz import timezone

class SpaBookingServiceWeb(http.Controller):

    @http.route('/page/spa_management/spa_booking_service_form', csrf=False, type='http', auth="public", website=True)
    def booking_service_info(self, **post):
        values = {}
        errors = dict()
        errors['name'] = ''

        fields = ['fullname','phonenumber', 'email', 'booking_day_time', 'booking_staff', 'request']

        # error message for empty required fi            
        for field_name in fields:
            values[field_name] = ''

        # Get product data
        data = self.get_service_info(post, errors, values)
        #_logger.info("Log get_service_info.times==================")
        #_logger.info(str(data['timeslots']))

        return request.render('spa_management.spa_booking_service_form', data)

    # Click Book    
    @http.route('/page/booking_service_register', csrf=False, type="http", methods=['POST', 'GET'], auth="public", website=True)
    def booking_service_register(self, **kwargs):
        _logger.debug("spa_booking>>kwargs: %s", str(kwargs))

        # Prevent error from F5
        if not kwargs or not kwargs['product_id']:
            return request.redirect('/') # redirect to home page
        
        # check inout form
        errors, error_msg = self.form_validate(kwargs)
    
        if errors:
            errors['error_message'] = error_msg
            post = dict(kwargs)
            #post['product_id'] = kwargs['product_id']
            #post['qty'] = kwargs["product_quantity"]

            # Get product data
            data = self.get_service_info(post, errors, kwargs)

            return request.render("spa_management.spa_booking_service_form", data)
        
        # No error process
        booking_day_time = kwargs['booking_day_time']
        product_duration = kwargs['product_duration'] # product_duration name
        
        date_start = datetime.strptime(booking_day_time, '%d/%m/%Y %H:%M')

        # get time for duration
        time_span = self.get_duration(product_duration)
        date_stop = date_start + timedelta(seconds=time_span)

        local_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        local_date_start = local_timezone.localize(date_start)
        local_date_stop = local_timezone.localize(date_stop)

        utc_timezone = pytz.timezone('UTC')
        utc_date_start = local_date_start.astimezone(utc_timezone)
        utc_date_stop = local_date_stop.astimezone(utc_timezone)

        utc_date_start_str = fields.Datetime.to_string(utc_date_start.astimezone(pytz.utc).replace(tzinfo=None))
        utc_date_stop_str = fields.Datetime.to_string(utc_date_stop.astimezone(pytz.utc).replace(tzinfo=None))


         # date start, date end - End
        # End by thanhtd
        # employees -Start
        employee_str = kwargs['booking_staff']
        spa_partner_ids = False
        
        if(employee_str):
            employee_list = employee_str.split(',')
            employees = []
            for employee_id in employee_list:
                employees.append(int(employee_id))           
            #spa_employee_obj = request.env['hr.employee'].search([('id', 'in', employees)]).work_contact_id.ids           
            #spa_employee_obj = request.env['hr.employee'].search([('work_contact_id', 'in', employees)]).work_contact_id.ids           
            #spa_partner_ids = spa_employee_obj
            spa_partner_ids = employees
            
        # default get the first employee in the list of employees
        else:
            # Get random who is available at this timeslot
            # Below is temp process (get first employee)
            spa_employee_obj = request.env['hr.employee'].search([]).work_contact_id.ids           
            spa_partner_ids = []
            spa_partner_ids.append(spa_employee_obj[0])       
                         
        # Get source="My Website" from utm.source
        source_data = request.env["utm.source"].search([('name', '=', 'My Website')])
        
        # employees -End
        spa_booking = request.env['spa.booking']
        booking_data = {
            'subject': kwargs['fullname'],
            'phone': kwargs['phonenumber'],
            'email': kwargs['email'],
            'date_start': utc_date_start_str,
            'date_stop': utc_date_stop_str,
            'service_ids': int(kwargs['product_id']), 
            'quantity': kwargs["product_quantity"],
            'partner_ids': spa_partner_ids,
            'remark': kwargs['request'],
            'source_id': int(source_data.id),
            'creator':'',
        }        

        _logger.debug("spa_booking booking_data: %s", str(booking_data))  
        spa_booking.create(booking_data)
        #return json.dumps({'result': True})
        return request.redirect('/page/spa_management/spa_booking_service_thank_you')


    @http.route('/page/spa_management/spa_booking_service_thank_you', type='http', auth="public", website=True)
    def thank_you(self, **post):
        return request.render('spa_management.spa_booking_service_thank_you', {})
            
    def get_service_info(self, post, errors, values):
        product_id = post['product_id']
        qty = post['product_quantity']
             
        booking_time = None
        if 'booking_time' in post:     
            booking_time = post['booking_time']

        select_date = datetime.now()
        #select_date = datetime.today().strftime('%d/%m/%Y')
        if 'booking_date' in post:
            #_logger.info("spa_booking pre select_date: %s", post['booking_date'])  
            select_date = datetime.strptime(post['booking_date'] , '%d/%m/%Y').date()

        booking_staff = None
        if 'booking_staff' in post and post['booking_staff'] :
            booking_staff = int(post['booking_staff'])  

        #_logger.info("spa_booking post select_date: %s",  str(select_date))      
        # get product data
        product =  request.env['product.product'].search([('id', 'in', [product_id])])
        list_price = product.list_price

        ptav = request.env["product.template.attribute.value"].search([("id", "=", product.combination_indices)])
        # Get duration name
        duration = request.env["product.attribute.value"].search([("id", "=", ptav.product_attribute_value_id.id)])
    
        price_extra = ptav.price_extra

        # Product -End
        # Calculate total -Start
        product_price = (float(list_price) + float(price_extra))
        product_total = int(qty) * product_price
        # Calculate total -End

        # Staff/Specialist
        spa_employee_obj = request.env['hr.employee'].search([('active', '=', True),('department_id.name', '=', 'KTV')])

        # get current date and default Staff/Specialist
        date = datetime.now().strftime('%Y-%m-%d')
        #spa_partner_obj = spa_employee_obj.work_contact_id.ids

        if not booking_staff:
            #partner_employee_id = [spa_employee_obj.work_contact_id.ids[0]]
            partner_employee_id = None
        else:
            partner_employee_id = [booking_staff]

        #_logger.info("spa_booking partner_employee_id: %s", partner_employee_id)  
        
        # get duration in seconds
        time_span = self.get_duration(duration.name)

        # get config's working hours
        working_times = self.get_working_hours()

        # "unbookable" : "Unbookable": is buffer time because service duration
        #working_status_times = {"booked" : "Hết Chỗ", "available": "Còn Chỗ" , "undefined" : "? Chỗ"}
        #timeslot_status = {"booked" : "Booked", "available": "Available" , "unbookable" : "Unbookable"}
        #if working_times:
        # Get timeslots: available timeslots and booked timeslots
        timeslots = self.get_timeslots(select_date, working_times, partner_employee_id, timedelta(seconds=time_span))
        
        data = {
            'product_id': product_id,
            'product_name': product.name,
            'product_quantity': qty,
            'product_price': product_price,
            'product_total': product_total,
            'product_duration': duration.name,
            'product_duration_id': duration.id,            
            'spa_employee_obj': spa_employee_obj.work_contact_id,
            'timeslots': timeslots,
            'book': values, # for keeping form input values when error
            'error':errors,

            # pass more these fields that keep selected on screen
            'booking_date': select_date.strftime('%d/%m/%Y'), # format DD/MM/YYY
            'booking_time': booking_time,
            'booking_day_time': values['booking_day_time'],
            'booking_staff': booking_staff
        }       
        
        return data 
    
    def form_validate(self, data):
        error = dict()
        error_message = []
        # Required fields        
        required_fields = ['fullname','phonenumber','booking_day_time']

        # error message for empty required fields
        for field_name in required_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # Phone validation
        if data.get('phonenumber'):
            phone_number = data.get('phonenumber').replace(" ","")      
            if not re.match("^[0-9]{10}$",phone_number):
                error["phonenumber"] = 'error'
                error_message.append(_('Invalid Phone! Please enter a valid phone number.'))

         # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(_('Invalid Email! Please enter a valid email address.'))    

        # date time validation
        if data.get('booking_day_time'):
            booking_day_time = data.get('booking_day_time')
            date_and_time = datetime.strptime(booking_day_time, '%d/%m/%Y %H:%M')

            if  date_and_time <= datetime.now():
                error["booking_day_time"] = 'error'
                error_message.append(_('Booking Date and Time must be greater than current date time.'))
            
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))            

        return error, error_message
    
    # Get config's working hours
    def get_working_hours(self):
        # Get start/end time ( default=Sunday)
        working_hours = request.env['spa.working.hours'].search([])
        times=[]
        if working_hours and working_hours[0]:
            working_time_default = working_hours[0]
            start_hour = int(working_time_default.from_time)
            start_minute = int((working_time_default.from_time - start_hour) * 60)
            end_hour = int(working_time_default.to_time)
            end_minute = int((working_time_default.to_time - end_hour) * 60)
            minute_interval = 30  # 30 minutes apart

            hour = start_hour
            minute = start_minute

            if start_hour != 0 and end_hour != 0:
                while hour < end_hour or (hour == end_hour and minute <= end_minute):
                    times.append({"time": f'{hour:02d}:{minute:02d}', "status": "unbookable"})

                    minute += minute_interval
                    if minute >= 60:
                        hour += 1
                        minute = minute % 60
        return times
    
    def get_timeslots(self, date, working_times, partner_employee, duration = timedelta(hours = 1)):
        """
        Get timeslots: booked timeslots and available timeslots
        @date: selected date
        @working_times: working times
        @partner_employee: selected staff/specialist
        @duration: service's duration

        """

        # get start/stop working hours
        working_hours_start = datetime.combine(date, datetime.strptime(working_times[0]["time"], "%H:%M").time())
        working_hours_stop = datetime.combine(date, datetime.strptime(working_times[-1]["time"], "%H:%M").time())

        date_start = datetime.combine(date, datetime.strptime("00:00:00", "%H:%M:%S").time())
        date_end = datetime.combine(date, datetime.strptime("23:59:59", "%H:%M:%S").time())

        # Get list of booked of employee at that date
        if partner_employee:
            # Get by employee
            spa_bookings = request.env['spa.booking'].search([('partner_ids', 'in', partner_employee), ('date_start', '>=', date_start), ('date_start', '<=', date_end)])
        else:
            # Get all employees
            #employees = request.env['hr.employee'].search([])
            spa_bookings = request.env['spa.booking'].search([('date_start', '>=', date_start), ('date_start', '<=', date_end)])

        booked_time_slots = []
        # Get list booked timeslots
        for booking in spa_bookings:
            booking_date_start = self.convert_to_localize_datetime(booking.date_start)
            booking_date_stop = self.convert_to_localize_datetime(booking.date_stop)

            booked_time_slots.append((booking_date_start, booking_date_stop))

        # Set start/stop of working_hours
        working_hours = (working_hours_start, working_hours_stop + duration)

        # get available timeslots
        available_time_slots = self.get_availability_timeslots(working_hours, booked_time_slots, duration)
        time_slots=(booked_time_slots, available_time_slots)

        # Set timeslot status (booked/available)
        working_times = self.set_timeslot_status(date, working_times, time_slots, duration)

        return working_times

    def get_availability_timeslots(self, hours, booked_time_slots, duration = timedelta(hours = 1)):
        """
            Get available timeslots
            @hours: working hour times (from to end)
            @booked_time_slots: already booked in db
            @duration: service's duration
        """
        available_time_slots = []
        slots = sorted([(hours[0], hours[0])] + booked_time_slots + [(hours[1], hours[1])])
        for start, end in ((slots[i][1], slots[i+1][0]) for i in range(len(slots)-1)):
            #assert start <= end, "Cannot attend all appointments"
            while start + duration <= end:
                available_time_slots.append((start, start + duration))
                start += duration

        return available_time_slots

    def set_timeslot_status(self, date_obj, working_times, time_slots, duration = timedelta(hours = 1)):
        """
        Set status (booked or available) to time slots
        @date_obj: now
        @working_times: working_times
        @time_slots: available time slots and booked time slots
        @duration: service's duration
        """
        working_end = datetime.combine(date_obj, datetime.strptime(working_times[-1]["time"], "%H:%M").time())
        # Filter booked time
        booked_time_slots = time_slots[0] 
        for slot in booked_time_slots:
            start_time = self.set_minute_to_zero(slot[0])
            end_time = self.set_minute_to_zero(slot[1])
            for item in working_times:
                time_object = datetime.strptime(item["time"], "%H:%M").time()
                date_time_object = datetime.combine(date_obj, time_object)
                if date_time_object >= start_time and date_time_object <= end_time:
                    item["status"] = "booked"

        # Filter available time slots
        # if the end time of the previous slot is equal to the start time of the current slot, join the current slot to the previous slot.
        available_time_slots = time_slots[1]
        collected_slots = []
        for slot in available_time_slots:
            if collected_slots and collected_slots[-1][1] == slot[0]:
                collected_slots[-1] = (collected_slots[-1][0], slot[1])
            else:
                collected_slots.append(slot)

        available_times = []        
        # filter available time to match slots and duration of service
        for slot in collected_slots:
            start_time = slot[0]
            end_time = slot[1]

            # loop config's working time
            for item in working_times:
                time_object = datetime.strptime(item["time"], "%H:%M").time()
                date_time_object = datetime.combine(date_obj, time_object)

                # get current time to set unavailble booking to past time
                now = self.convert_to_localize_datetime(datetime.now())

                # if time <= current time, set booked time
                if date_time_object <= now:
                    item["status"] = "booked"
                else:
                    # if final slot and end time of final slot >= wroking time end, need to add duration from wroking time end to compare
                    if(slot == collected_slots[-1] and end_time >= working_end and item["status"] != 'booked'):
                        if( date_time_object >= start_time and date_time_object <= working_end + duration):
                            item["status"] = "available"
                    # filter available time to match slots and duration of service
                    elif date_time_object >= start_time and date_time_object <= end_time  and date_time_object + duration <= end_time:
                            item["status"] = "available"
                    else:
                        # skip, do nothing
                        continue
                    
        return working_times

    
    def convert_to_localize_datetime(self, date):
        """
        Convert datetime to localize datetime
        """

        # Define the source and destination timezones
        source_timezone = pytz.utc
        destination_timezone = pytz.timezone('Asia/Ho_Chi_Minh')

        # Convert UTC time to local time in Asia/Ho_Chi_Minh timezone
        local_date = date.replace(tzinfo = source_timezone).astimezone(destination_timezone)
        # Convert to simple datetime object
        date_object = local_date.replace(tzinfo = None)

        return date_object
        
    # set datetime when minute >=0 and minute < 30
    def set_minute_to_zero(self, datetime):
        if datetime.minute >= 0 and datetime.minute < 30:
            datetime = datetime.replace(minute=0)
        return datetime
    
    # get duration of a service
    def get_duration(self, product_duration):
        if(product_duration):
            duration = product_duration.split(" ")
            time_span = int(duration[0])
            time_unit = duration[1]

            if(time_unit.lower() == "minutes" or time_unit.lower() == "phút"):
                time_span = time_span*60
        # return duration in seconds
        return time_span