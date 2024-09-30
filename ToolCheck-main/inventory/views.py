from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserRegisterForm, InventoryItemForm
from .forms import NotificationPreferenceForm
from .models import InventoryItem, Category
from .models import NotificationPreference
from inventory_management.settings import LOW_QUANTITY
from django.contrib import messages
from django.shortcuts import get_object_or_404


class Index(TemplateView):
	template_name = 'inventory/index.html'

class Dashboard(LoginRequiredMixin, View):
    def get(self, request):
        items = InventoryItem.objects.filter(user=self.request.user.id).order_by('id')
        low_inventory = InventoryItem.objects.filter(
            user=self.request.user.id,
            quantity__lte=LOW_QUANTITY
        )

        # This will either get the existing NotificationPreference or create one if it doesn't exist
        preference, created = NotificationPreference.objects.get_or_create(user=request.user)

        if preference.notify_on_low_inventory and low_inventory.count() > 0:
            if low_inventory.count() > 1:
                messages.error(request, f'{low_inventory.count()} items have low inventory')
            else:
                messages.error(request, f'{low_inventory.count()} item has low inventory')

        low_inventory_ids = low_inventory.values_list('id', flat=True)

        return render(request, 'inventory/dashboard.html', {'items': items, 'low_inventory_ids': low_inventory_ids})


class SignUpView(View):
    def get(self, request):
        form = UserRegisterForm()
        return render(request, 'inventory/signup.html', {'form': form})

    def post(self, request):
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            # Create NotificationPreference for the new user
            NotificationPreference.objects.create(user=user)

            login(request, user)
            return redirect('index')

        return render(request, 'inventory/signup.html', {'form': form})
	
class NotificationPreferenceView(LoginRequiredMixin, View):
    template_name = 'inventory/notification_preferences.html'

    def get(self, request):
        preference, created = NotificationPreference.objects.get_or_create(user=request.user)
        form = NotificationPreferenceForm(instance=preference)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        preference = get_object_or_404(NotificationPreference, user=request.user)
        form = NotificationPreferenceForm(request.POST, instance=preference)

        if form.is_valid():
            form.save()
            messages.success(request, 'Notification preferences updated successfully.')
            return redirect('dashboard')

        return render(request, self.template_name, {'form': form})

class AddItem(LoginRequiredMixin, CreateView):
	model = InventoryItem
	form_class = InventoryItemForm
	template_name = 'inventory/item_form.html'
	success_url = reverse_lazy('dashboard')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['categories'] = Category.objects.all()
		return context

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)

class EditItem(LoginRequiredMixin, UpdateView):
	model = InventoryItem
	form_class = InventoryItemForm
	template_name = 'inventory/item_form.html'
	success_url = reverse_lazy('dashboard')

class DeleteItem(LoginRequiredMixin, DeleteView):
	model = InventoryItem
	template_name = 'inventory/delete_item.html'
	success_url = reverse_lazy('dashboard')
	context_object_name = 'item'
