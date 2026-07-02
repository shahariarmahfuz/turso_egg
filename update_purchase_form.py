import os

with open('/workspaces/egg/templates/purchase_form.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Partial option
content = content.replace('<option value="Due">Due</option>', '<option value="Due">Due</option>\n                        <option value="Partial">Partial</option>')

# Update Javascript
old_js = """        let isCash = $('#payment_method').val() === 'Cash';
        if(isCash) { $('#cash_paid').val(grandTotal.toFixed(2)); }

        let paid = parseFloat($('#cash_paid').val()) || 0;
        let due = grandTotal - paid;
        if(due < 0) due = 0;
        $('#due_amount').val(due.toFixed(2));"""

new_js = """        let method = $('#payment_method').val();
        if(method === 'Cash') {
            $('#cash_paid').val(grandTotal.toFixed(2));
            $('#cash_paid').prop('readonly', true);
            $('#due_amount').prop('readonly', true);
        } else if (method === 'Due') {
            $('#cash_paid').val('0.00');
            $('#cash_paid').prop('readonly', true);
            $('#due_amount').val(grandTotal.toFixed(2));
            $('#due_amount').prop('readonly', true);
        } else {
            $('#cash_paid').prop('readonly', false);
            $('#due_amount').prop('readonly', false);
        }

        let paid = parseFloat($('#cash_paid').val()) || 0;
        if (paid > grandTotal) {
            paid = grandTotal;
            $('#cash_paid').val(paid.toFixed(2));
        }
        let due = grandTotal - paid;
        if(due < 0) due = 0;
        $('#due_amount').val(due.toFixed(2));"""

content = content.replace(old_js, new_js)

# Add event listeners for cash_paid and due_amount like sale_form
new_listeners = """    $('#cash_paid').on('input', function() {
        let grandTotal = parseFloat($('#grand_total').val()) || 0;
        let paid = parseFloat($(this).val()) || 0;
        if (paid > grandTotal) {
            alert("Cash Paid cannot exceed the payable amount!");
            paid = grandTotal;
            $(this).val(paid.toFixed(2));
        }
        if (paid < 0) {
            paid = 0;
            $(this).val(paid.toFixed(2));
        }
        let due = grandTotal - paid;
        $('#due_amount').val(due.toFixed(2));
    });

    $('#due_amount').on('input', function() {
        let grandTotal = parseFloat($('#grand_total').val()) || 0;
        let due = parseFloat($(this).val()) || 0;
        if (due > grandTotal) {
            due = grandTotal;
            $(this).val(due.toFixed(2));
        }
        if (due < 0) {
            alert("Due Amount cannot be negative!");
            due = 0;
            $(this).val(due.toFixed(2));
        }
        let paid = grandTotal - due;
        $('#cash_paid').val(paid.toFixed(2));
    });

    function calculateTotals() {"""

content = content.replace('    function calculateTotals() {', new_listeners)

# Also remove readonly from due_amount field so it can be edited
content = content.replace('<input type="text" class="form-control fw-bold" id="due_amount" readonly value="0.00">', '<input type="number" step="0.01" min="0" class="form-control calc-input fw-bold" id="due_amount" name="due_amount" value="0.00">')

with open('/workspaces/egg/templates/purchase_form.html', 'w', encoding='utf-8') as f:
    f.write(content)
