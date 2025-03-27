odoo.define("spa_managerment.custom", function (require) {
    "use strict";

    // Tool for patch modules
    const { patch } = require("@web/core/utils/patch");

    // Modules that need to patched
    var { CalendarFilterPanel } = require('@web/views/calendar/filter_panel/calendar_filter_panel');

    // For patch CalendarFilterPanel
    patch(CalendarFilterPanel.prototype, "Patch for CalendarFilterPanel", {
        // Extends --------------------------------------------------------------
        /**
         * Overwrite loadSource() of CalendarFilterPanel
         */        
        async loadSource(section, request) {
            var parentSuper = this._super;
            if (this.props.model.meta.resModel === 'spa.booking'){
                // ================ Staffs for calendar who belong to 'KTV' department ===================
                // get list of employee
                const employee = await this.orm.searchRead('hr.employee', [], [
                    'id',
                    'work_contact_id',
                    'department_id',
                    'active'
                ], {});


                // Calc list of partner id that is employee
                var employeePartnerIds = [];
                employee.map(function(employeeItem){
                    // Check if it belong to "KTV" department
                    if (employeeItem.work_contact_id.length > 0 && employeeItem.department_id.length > 0){     
                        // If employee belong to 'KTV' and activating        
                        // department_id[1] may be = XXX/ KTV if XXX is parent dept of KTV                                 
                        if (employeeItem.department_id[1].includes("KTV") && employeeItem.active) {                                          
                            employeePartnerIds.push(employeeItem.work_contact_id[0]);
                        }
                    }
                });


                // Get list partner is not employee
                const partnerNotEmployee = await this.orm.searchRead('res.partner', [['id', 'not in', employeePartnerIds]], ['id',], {});
                //Set list of non employee to section.filters. This is the list that don't show in Staffs/Specialists box
                partnerNotEmployee.map(function(partnerNotEmployeeItem){
                    // 20230322 add check by Lam. push if not exist (=== -1)
                    if (section.filters.findIndex(item=>item.value == partnerNotEmployeeItem.id) === -1) {
                        section.filters.push({
                            type: 'record',
                            value: partnerNotEmployeeItem.id
                        });
                    }
                });
                
            }
            // Call parent to take action filter for get employee
            var options = await parentSuper(section, request);

            return options;
        },

        /**
         * Overwrite getSortedFilters() of CalendarFilterPanel
         */
        getSortedFilters(section) {
            // Filter section.filters before call parent to process
            if (this.props.model.meta.resModel == 'spa.booking') {
                // By hiding Login user and Everybody's calendars from Staffs/Specialist section (checkbox list)
                section.filters = section.filters.filter(item => item.type != 'user' && item.type != 'all' );
            }
            // Call super
            return this._super(section);
        }
    });
});