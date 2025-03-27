odoo.define('spa_management.website_spa_booking_service', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var QWeb = core.qweb;

    // Shorthand for $( document ).ready()
    $(function() {
        // Set current date (today)
        const selected_date = $('#booking_date').val();
        if (selected_date == '' || selected_date == undefined) {
            $('#booking_date').val(moment().format('DD/MM/YYYY'));
        }

        // $( "#datepicker" ).datepicker({
        //     showButtonPanel: true,
        //     minDate: 0, // today or new Date()
        //     onSelect: function (date, datepicker) {
        //         if (date != "") {
        //             // Clear date input
        //             $('#booking_day_time').val('');  
        //             const selected_date = moment(date, "MM/DD/YYYY").format('DD/MM/YYYY') // datepicker date format: MM/DD/YYYY

        //             // Set to hidden 'selected_date'                    
        //             $('#booking_date').val(selected_date);                        
                    
        //             // Submit data
        //             const data = {
        //                 product_id : $('#product_id').val(),
        //                 product_quantity: $('#product_quantity').val(),
        //                 booking_staff: $('#booking_staff').val(),
        //                 booking_date: selected_date

        //             };
        //             // Call Ajax get
        //             doAjax("/page/spa_management/spa_booking_service_form", "get", data);
                  
        //         }
        //     }

        // });
        // Not works here. Move to spa_booking_service_templates.xml
        //$("#datepicker").datepicker( $.datepicker.regional[ "vi" ] );
        // $(document).ready(function() {
        //     // Init calendar translate 
        //     $("#datepicker").datepicker( $.datepicker.regional[ "vi" ] );
        // });

        /**
         * Staff/Specialist change event
         */
        $('#booking_staff').on('change', function() {
            //const selected_date =  $( "#datepicker" ).datepicker("getDate"); // not work here
            const selected_date = $('#booking_date').val();
             
            // Submit data
            const data = {
                product_id : $('#product_id').val(),
                product_quantity: $('#product_quantity').val(),
                booking_date: selected_date, //moment(selected_date).format('DD/MM/YYYY'),
                booking_staff: $(this).find(":selected").val() // selected radio val
            };
    
            // Call Ajax get
            doAjax("/page/spa_management/spa_booking_service_form", "get", data);
             
        });           
    

        /**
         * Book click event
         */        
        $('#book_now').on('click', function (ev) {
            debugger
    
            var product_id=$('input[name="product_id"]').val();
            var product_quantity=$('input[name="add_qty"]').val();
    
            var product_href="/page/spa_management/spa_booking_service_form?product_id="+product_id+"&product_quantity="+product_quantity
            window.location.href = product_href;
        });        
    })

    /**
     * Available timeslot click event
     * Note: not works if move this to block "$(function() {}". Keep here
     */
    $(document).on('click', 'label.available', function() {
        debugger;
        // Clear booking datetime value
        $('#booking_day_time').val('');  

        // Get date
        const selected_date = $('#booking_date').val();

        var selected_time = $(this).children().first().text(); // get value of first <span> 
        // Set selected radio. if there no selected_time on un available timeslots
        $("input[type='radio'][id='"+selected_time+"']").prop('checked',true)
        // Get radio value
        selected_time = $("input[type='radio'][id='"+selected_time+"']").val();

        // Set if exist value. undefined if get on != available timeslots
        if (selected_time != '' && selected_time != undefined) {
            // Set date + ' ' + time
            $('#booking_day_time').val(selected_date + ' ' + selected_time);  
            $('#booking_time').val(selected_time);  
        }
    });


    function doAjax(url, method, data) {
        $.ajax({
            url :  url,
            type: method,
            dataType : "html",
            data : data,
            beforeSend : function(){
                $('.spinner-loading').show();
            },
            complete : function(){
                $('.spinner-loading').hide();
            },            
            success: function (data){
                //console.log("SUCCESS : ", data);
                //get id=timeslots from data                            
                // set result to current #timeslots
                $("#timeslots").html($(data).find('#timeslots').html());
            },
            error: function (e) {

                var json = "<h4>Ajax Response</h4><pre>"
                    + e.responseText + "</pre>";
                $('#timeslots').html(json);

                //console.log("ERROR : ", e);
            }                        
        });        
    }
});
