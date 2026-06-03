document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".budget-form").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            var budgetInput = form.querySelector("#budget");
            var errors = [];

            if (budgetInput) {
                var value = parseFloat(budgetInput.value);
                if (!budgetInput.value.trim()) {
                    errors.push("Budget cannot be empty.");
                } else if (Number.isNaN(value) || value <= 0) {
                    errors.push("Budget must be a positive number.");
                }
            }

            if (errors.length > 0) {
                event.preventDefault();
                alert(errors.join("\n"));
            }
        });
    });

    document.querySelectorAll(".delete-form").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            var confirmed = window.confirm(
                "Are you sure you want to delete this expense? This action cannot be undone."
            );
            if (!confirmed) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll(".expense-form").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            var title = form.querySelector("#title");
            var amount = form.querySelector("#amount");
            var category = form.querySelector("#category");
            var dateInput = form.querySelector("#date");
            var errors = [];

            if (title && !title.value.trim()) {
                errors.push("Title is required.");
            }

            if (amount) {
                var value = parseFloat(amount.value);
                if (!amount.value.trim()) {
                    errors.push("Amount is required.");
                } else if (Number.isNaN(value) || value <= 0) {
                    errors.push("Amount must be a positive number.");
                }
            }

            if (category && !category.value) {
                errors.push("Category is required.");
            }

            if (dateInput && dateInput.value) {
                var selected = new Date(dateInput.value + "T00:00:00");
                var today = new Date();
                today.setHours(0, 0, 0, 0);
                if (selected > today) {
                    errors.push("Future dates are not allowed.");
                }
            } else if (dateInput) {
                errors.push("Date is required.");
            }

            if (errors.length > 0) {
                event.preventDefault();
                alert(errors.join("\n"));
            }
        });
    });
});
