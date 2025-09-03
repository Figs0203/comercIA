from django.contrib import admin
from .models import SellerProfile, Schedule

class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'slogan')
    search_fields = ('store_name', 'user__username')
    inlines = [ScheduleInline]

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('profile', 'day', 'start_time', 'end_time')
    list_filter = ('day',)
