from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Leave
from .forms import LeaveRequestForm
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, UpdateView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

class LeaveRequestListView(LoginRequiredMixin, ListView):
    model = Leave
    template_name = 'leaves/leave_history.html'
    context_object_name = 'leaves'

    def get_queryset(self):
        return Leave.objects.filter(employee=self.request.user).order_by('-applied_at')

class LeaveRequestCreateView(LoginRequiredMixin, CreateView):
    model = Leave
    form_class = LeaveRequestForm
    template_name = 'leaves/apply_leave.html'
    success_url = reverse_lazy('leaves:leave_history')

    def form_valid(self, form):
        form.instance.employee = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""
        return self.render_to_response(self.get_context_data(form=form))

    def get_form_kwargs(self):  # Pass user to the form
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):  # Send success message from CreateView
        context = super().get_context_data(**kwargs)
        if 'success_message' in self.request.GET:
            context['success_message'] = self.request.GET['success_message']
        return context


class LeaveRequestUpdateView(LoginRequiredMixin, UpdateView):
    model = Leave
    form_class = LeaveRequestForm
    template_name = 'leaves/apply_leave.html'
    success_url = reverse_lazy('leaves:leave_history')

    def get_queryset(self):
        return Leave.objects.filter(employee=self.request.user)

    def form_valid(self, form):
        form.instance.employee = self.request.user  # Even in update view, keep this line for safety
        return super().form_valid(form)

    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""
        return self.render_to_response(self.get_context_data(form=form))

    def get_form_kwargs(self):  # Pass user to the form (same as in CreateView)
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


@login_required
def cancel_leave(request, pk):
    leave = get_object_or_404(Leave, pk=pk, employee=request.user) # Ensure it's the user's leave
    if leave.status == 'Pending':
        if request.method == 'POST':  # Handle POST request for confirmation
            leave.status = 'Cancelled'
            leave.save()
            messages.success(request, "Leave request cancelled.")
            return redirect('leaves:leave_history')  # Redirect back to history

        # GET request: Render a confirmation page
        return render(request, 'leaves/cancel_leave_confirm.html', {'leave': leave})
    else:
        messages.error(request, "Cannot cancel a leave request that is not pending.")
        return redirect('leaves:leave_history')