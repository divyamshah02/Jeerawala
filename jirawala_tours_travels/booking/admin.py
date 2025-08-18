from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from .models import CarType, Car, PopularRoute, Inquiry, BookingStatusHistory, Gallery
import datetime
import base64

try:
    @admin.register(Gallery)
    class GalleryAdmin(admin.ModelAdmin):
        list_display = ['title', 'description_short', 'display_order', 'is_active', 'image_preview', 'created_at']
        list_filter = ['is_active', 'created_at']
        search_fields = ['title', 'description']
        readonly_fields = ['created_at', 'updated_at', 'image_preview']
        list_editable = ['display_order', 'is_active']
        ordering = ['display_order', '-created_at']
        
        fieldsets = (
            ('Gallery Information', {
                'fields': ('title', 'description', 'display_order', 'is_active')
            }),
            ('Image Management', {
                'fields': ('image_upload', 'image_preview', 'image_filename', 'image_content_type'),
                'description': 'Upload new images or view current image. Images are stored in database.'
            }),
            ('Timestamps', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )
        
        def get_form(self, request, obj=None, **kwargs):
            """Customize the admin form"""
            form = super().get_form(request, obj, **kwargs)
            
            # Add custom image upload field
            from django import forms
            form.base_fields['image_upload'] = forms.ImageField(
                required=False,
                help_text='Upload a new image to replace the current one. Images are stored in database.',
                widget=forms.ClearableFileInput(attrs={'accept': 'image/*'})
            )
            
            return form
        
        def description_short(self, obj):
            """Display shortened description"""
            if obj.description:
                return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
            return "No description"
        description_short.short_description = 'Description'
        
        def image_preview(self, obj):
            """Display image preview in admin"""
            if obj and obj.pk and obj.image_data:
                try:
                    data_url = obj.get_image_data_url()
                    if data_url:
                        return mark_safe(
                            f'<img src="{data_url}" style="max-width: 150px; max-height: 150px; border: 1px solid #ddd; border-radius: 4px;" />'
                            f'<br><small>Stored in database ({len(obj.image_data)} bytes)</small>'
                        )
                except Exception as e:
                    return f"Error loading image: {str(e)}"
            return "No image"
        image_preview.short_description = 'Current Image'
        
        def save_model(self, request, obj, form, change):
            """Handle image upload when saving"""
            # Check if new image was uploaded
            if 'image_upload' in form.cleaned_data and form.cleaned_data['image_upload']:
                uploaded_file = form.cleaned_data['image_upload']
                obj.set_image_from_file(uploaded_file)
            
            super().save_model(request, obj, form, change)
except admin.sites.AlreadyRegistered:
    pass

class StatusHistoryInline(admin.TabularInline):
    model = BookingStatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'changed_at')
    can_delete = False


class TripTypeFilter(SimpleListFilter):
    title = 'Trip Type'
    parameter_name = 'trip_type'

    def lookups(self, request, model_admin):
        return Inquiry.TRIP_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(trip_type=self.value())
        return queryset


class StatusFilter(SimpleListFilter):
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return Inquiry.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class DateRangeFilter(SimpleListFilter):
    title = 'Booking Date'
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('yesterday', 'Yesterday'),
            ('this_week', 'This Week'),
            ('this_month', 'This Month'),
            ('last_month', 'Last Month'),
        )

    def queryset(self, request, queryset):
        today = datetime.date.today()
        if self.value() == 'today':
            return queryset.filter(created_at__date=today)
        elif self.value() == 'yesterday':
            yesterday = today - datetime.timedelta(days=1)
            return queryset.filter(created_at__date=yesterday)
        elif self.value() == 'this_week':
            start_week = today - datetime.timedelta(days=today.weekday())
            return queryset.filter(created_at__date__gte=start_week)
        elif self.value() == 'this_month':
            return queryset.filter(created_at__year=today.year, created_at__month=today.month)
        elif self.value() == 'last_month':
            last_month = today.replace(day=1) - datetime.timedelta(days=1)
            return queryset.filter(created_at__year=last_month.year, created_at__month=last_month.month)
        return queryset


@admin.register(CarType)
class CarTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate_per_km', 'minimum_distance_cap', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['name', 'car_type', 'is_available', 'image_preview']
    list_filter = ['car_type', 'is_available']
    search_fields = ['name']
    readonly_fields = ['created_at', 'image_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'car_type', 'is_available')
        }),
        ('Image Management', {
            'fields': ('image_upload', 'image_preview', 'image_filename', 'image_content_type'),
            'description': 'Upload new images or view current image. Images are stored in database.'
        }),
        ('Legacy Image (Deprecated)', {
            'fields': ('image',),
            'classes': ('collapse',),
            'description': 'Old file-based image field. Will be removed after migration.'
        }),
        ('Legacy Fields (Hidden)', {
            'fields': ('registration_number', 'driver_name', 'driver_contact'),
            'classes': ('collapse',),
            'description': 'Legacy fields that are no longer used in the frontend but kept for database compatibility.'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize the admin form"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add custom image upload field
        from django import forms
        form.base_fields['image_upload'] = forms.ImageField(
            required=False,
            help_text='Upload a new image to replace the current one. Images are stored in database.',
            widget=forms.ClearableFileInput(attrs={'accept': 'image/*'})
        )
        
        return form
    
    def image_preview(self, obj):
        """Display image preview in admin"""
        if obj and obj.pk:
            try:
                # Check for BLOB image data first
                if obj.image_data and obj.image_content_type:
                    # Use database image
                    data_url = obj.get_image_data_url()
                    if data_url:
                        return mark_safe(
                            f'<img src="{data_url}" style="max-width: 150px; max-height: 150px; border: 1px solid #ddd; border-radius: 4px;" />'
                            f'<br><small>Stored in database ({len(obj.image_data)} bytes)</small>'
                        )
                # Check for file-based image
                elif obj.image and hasattr(obj.image, 'url'):
                    try:
                        return mark_safe(
                            f'<img src="{obj.image.url}" style="max-width: 150px; max-height: 150px; border: 1px solid #ddd; border-radius: 4px;" />'
                            f'<br><small>File-based (legacy)</small>'
                        )
                    except:
                        pass
            except Exception as e:
                return f"Error loading image: {str(e)}"
        return "No image"
    image_preview.short_description = 'Current Image'
    
    def save_model(self, request, obj, form, change):
        """Handle image upload when saving"""
        # Check if new image was uploaded
        if 'image_upload' in form.cleaned_data and form.cleaned_data['image_upload']:
            uploaded_file = form.cleaned_data['image_upload']
            obj.set_image_from_file(uploaded_file)
        
        super().save_model(request, obj, form, change)


@admin.register(PopularRoute)
class PopularRouteAdmin(admin.ModelAdmin):
    list_display = ['origin', 'destination', 'rate', 'distance_km', 'is_active', 'image_preview', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['origin', 'destination']
    readonly_fields = ['created_at', 'image_preview']
    
    fieldsets = (
        ('Route Information', {
            'fields': ('origin', 'destination', 'distance_km', 'rate', 'is_active')
        }),
        ('Image Management', {
            'fields': ('image_upload', 'image_preview', 'image_filename', 'image_content_type'),
            'description': 'Upload new images or view current image. Images are stored in database.'
        }),
        ('Legacy Image (Deprecated)', {
            'fields': ('image',),
            'classes': ('collapse',),
            'description': 'Old file-based image field. Will be removed after migration.'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize the admin form"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add custom image upload field
        from django import forms
        form.base_fields['image_upload'] = forms.ImageField(
            required=False,
            help_text='Upload a new image to replace the current one. Images are stored in database.',
            widget=forms.ClearableFileInput(attrs={'accept': 'image/*'})
        )
        
        return form
    
    def image_preview(self, obj):
        """Display image preview in admin"""
        if obj and obj.pk:
            try:
                # Check for BLOB image data first
                if obj.image_data and obj.image_content_type:
                    # Use database image
                    data_url = obj.get_image_data_url()
                    if data_url:
                        return mark_safe(
                            f'<img src="{data_url}" style="max-width: 150px; max-height: 150px; border: 1px solid #ddd; border-radius: 4px;" />'
                            f'<br><small>Stored in database ({len(obj.image_data)} bytes)</small>'
                        )
                # Check for file-based image
                elif obj.image and hasattr(obj.image, 'url'):
                    try:
                        return mark_safe(
                            f'<img src="{obj.image.url}" style="max-width: 150px; max-height: 150px; border: 1px solid #ddd; border-radius: 4px;" />'
                            f'<br><small>File-based (legacy)</small>'
                        )
                    except:
                        pass
            except Exception as e:
                return f"Error loading image: {str(e)}"
        return "No image"
    image_preview.short_description = 'Current Image'
    
    def save_model(self, request, obj, form, change):
        """Handle image upload when saving"""
        # Check if new image was uploaded
        if 'image_upload' in form.cleaned_data and form.cleaned_data['image_upload']:
            uploaded_file = form.cleaned_data['image_upload']
            obj.set_image_from_file(uploaded_file)
        
        super().save_model(request, obj, form, change)


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = [
        'booking_id', 'customer_info_safe', 'route_info_safe', 'pickup_date_safe', 
        'car_type', 'status_badge_safe', 'price_safe', 'created_at'
    ]
    list_filter = [StatusFilter, TripTypeFilter, 'car_type', DateRangeFilter, 'created_at', 'is_active']
    search_fields = ['booking_id', 'name', 'email', 'number', 'origin', 'destination']
    readonly_fields = ['booking_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'email', 'number')
        }),
        ('Trip Details', {
            'fields': ('trip_type', 'origin', 'destination', 'datetime', 'return_datetime')
        }),
        ('Vehicle & Pricing', {
            'fields': ('car_type', 'assigned_car', 'distance_km', 'price')
        }),
        ('Booking Management', {
            'fields': ('status', 'booking_id', 'is_active')
        }),
        ('Additional Information', {
            'fields': ('special_requests', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [StatusHistoryInline]
    
    actions = ['mark_as_confirmed', 'mark_as_in_progress', 'mark_as_completed', 'mark_as_cancelled']
    
    def customer_info_safe(self, obj):
        try:
            name = obj.name or "N/A"
            email = obj.email or "N/A"
            number = obj.number or "N/A"
            
            html = '<strong>' + str(name) + '</strong><br>'
            html += '<small>📧 ' + str(email) + '</small><br>'
            html += '<small>📱 ' + str(number) + '</small>'
            
            return mark_safe(html)
        except:
            return "Error loading customer info"
    customer_info_safe.short_description = 'Customer'
    
    def route_info_safe(self, obj):
        try:
            origin = obj.origin or "N/A"
            destination = obj.destination or "N/A"
            distance = obj.distance_km or 0
            
            html = '<strong>' + str(origin) + '</strong><br>'
            html += '<small>↓</small><br>'
            html += '<strong>' + str(destination) + '</strong><br>'
            html += '<small>📏 ' + str(round(float(distance), 1)) + ' km</small>'
            
            return mark_safe(html)
        except:
            return "Error loading route info"
    route_info_safe.short_description = 'Route'
    
    def pickup_date_safe(self, obj):
        try:
            if obj.datetime:
                date_str = obj.datetime.strftime('%Y-%m-%d')
                time_str = obj.datetime.strftime('%H:%M')
                html = '<strong>' + date_str + '</strong><br>'
                html += '<small>' + time_str + '</small>'
                return mark_safe(html)
            return "N/A"
        except:
            return "Error loading date"
    pickup_date_safe.short_description = 'Pickup Date/Time'
    
    def price_safe(self, obj):
        try:
            if obj.price:
                price_str = "₹{:,.2f}".format(float(obj.price))
                return price_str
            return "₹0.00"
        except:
            return "Error loading price"
    price_safe.short_description = 'Price'
    
    def status_badge_safe(self, obj):
        try:
            status_colors = {
                'pending': '#ffc107',
                'confirmed': '#28a745',
                'in_progress': '#17a2b8',
                'completed': '#6c757d',
                'cancelled': '#dc3545',
            }
            
            color = status_colors.get(obj.status, '#6c757d')
            status_text = obj.get_status_display().upper() if obj.status else 'UNKNOWN'
            
            html = '<span style="background-color: ' + color + '; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">'
            html += str(status_text)
            html += '</span>'
            
            return mark_safe(html)
        except:
            return obj.status or "Unknown"
    status_badge_safe.short_description = 'Status'
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, 'Updated {} bookings to confirmed.'.format(updated))
    mark_as_confirmed.short_description = "Mark selected bookings as confirmed"
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, 'Updated {} bookings to in progress.'.format(updated))
    mark_as_in_progress.short_description = "Mark selected bookings as in progress"
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, 'Updated {} bookings to completed.'.format(updated))
    mark_as_completed.short_description = "Mark selected bookings as completed"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, 'Updated {} bookings to cancelled.'.format(updated))
    mark_as_cancelled.short_description = "Mark selected bookings as cancelled"


@admin.register(BookingStatusHistory)
class BookingStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['inquiry', 'old_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['old_status', 'new_status', 'changed_at']
    search_fields = ['inquiry__booking_id', 'inquiry__name']
    readonly_fields = ['changed_at']


# Custom admin site configuration
admin.site.site_header = "Jirawala Tours & Travels Admin"
admin.site.site_title = "Jirawala Admin"
admin.site.index_title = "Booking Management System"
