{
    "name": "Sprite Full Calendar",
    "summary": "Sprite Vertical Resource View",
    "version": "16.1.0.0.0",
    "author": "Sprite plus",
    'company': 'Sprite plus',
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "calendar",
        "web"
    ],
    'assets': {
        'web.assets_backend': [
            'sprite_fullcalendar/static/lib/packages/core/main.js',
            'sprite_fullcalendar/static/lib/packages/interaction/main.js',            
            'sprite_fullcalendar/static/lib/packages/luxon/main.js',   
            'sprite_fullcalendar/static/lib/packages/daygrid/main.js',
            'sprite_fullcalendar/static/lib/packages/timegrid/main.js',            

            'sprite_fullcalendar/static/lib/premium/resource-common/main.js',
            'sprite_fullcalendar/static/lib/premium/resource-daygrid/main.js',
            'sprite_fullcalendar/static/lib/premium/resource-timegrid/main.js',

            'sprite_fullcalendar/static/src/custom.js',            
            'sprite_fullcalendar/static/src/custom.css',

            'sprite_fullcalendar/static/lib/packages/daygrid/main.css',
            'sprite_fullcalendar/static/lib/packages/timegrid/main.css',
        ],
    },
}
