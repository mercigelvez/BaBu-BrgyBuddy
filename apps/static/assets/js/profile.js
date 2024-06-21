$(document).ready(function () {
  fetchCurrentUserData();

  $('#editProfileBtn').click(function () {
    $('#usernameInput, #currentPasswordInput, #newPasswordInput, #saveChangesBtn').removeAttr('disabled');
    $('#saveChangesBtn').show(); // Show the "Save Changes" button
    $(this).hide(); // Hide the "Edit" button

    // Add event listeners for real-time validation
    $('#profileForm input').on('input', function () {
      validateInput(this);
    });

    // Add event listener for username validation
    $('#usernameInput').on('input', function () {
      validateUsername(currentUsername);
    });

    // Add event listener for current password validation
    $('#currentPasswordInput').on('input', function () {
      validateCurrentPassword();
    });

    // Add event listener for new password validation
    $('#newPasswordInput').on('input', validateNewPassword);
  });

  $('#saveChangesBtn').click(function (e) {
    e.preventDefault(); // Prevent the form from submitting

    // Check if all required fields are valid
    let isValid = true;
    $('#profileForm input[required]').each(function () {
      if (!this.checkValidity()) {
        isValid = false;
        $(this).addClass('is-invalid');
      } else {
        $(this).removeClass('is-invalid');
      }
    });

    // If all fields are valid, show the confirmation modal
    if (isValid) {
      $('#profilenModal').modal('hide');
      $('#confirmationModal').modal('show');
    }
  });

  $('#confirmSaveChanges').click(function () {
    // Send AJAX request to check current password
    $.ajax({
      url: '/check_current_password',
      type: 'POST',
      data: { current_password: $('#currentPasswordInput').val() },
      contentType: 'application/x-www-form-urlencoded; charset=UTF-8',
      success: function (data) {
        if (data.is_valid) {
          // If the current password is valid, submit the form
          $('#profileForm').submit();
          // Hide the confirmation modal
          $('#confirmationModal').modal('hide');
          // Show the "Save Changes" modal after form submission
          $('#saveChangesModal').modal('show');
        } else {
          const currentPasswordErrorMessage = $('#currentPasswordInput').siblings('.invalid-feedback');
          currentPasswordErrorMessage.text('Incorrect current password.');
          $('#currentPasswordInput').addClass('is-invalid');
          // Hide the confirmation modal
          $('#confirmationModal').modal('hide');
        }
      },
      error: function (xhr, status, error) {
        console.error('Error checking current password:', error);
        // Hide the confirmation modal
        $('#confirmationModal').modal('hide');
      }
    });
  });

  // Reset form validation when the modal is closed
  $('#profileModal').on('hidden.bs.modal', function () {
    // Remove any error validations
    $('input.form-control').removeClass('is-invalid');
    $('.invalid-feedback').text('');

    // Reset input field values
    $('#usernameInput').val(currentUsername.trim()); // Replace with the actual current username value and trim it
    $('#currentPasswordInput').val('');
    $('#newPasswordInput').val('');

    // Hide the "Save Changes" button
    $('#saveChangesBtn').hide();

    // Show the "Edit" button
    $('#editProfileBtn').show();

    // Disable the input fields
    $('#usernameInput, #currentPasswordInput, #newPasswordInput').attr('disabled', 'disabled');
  });

  // Fetch the current user's information when the modal is opened
  $('#profileModal').on('show.bs.modal', function () {
    fetchCurrentUserData();
  });
});

function validateInput(input) {
  if (input.checkValidity()) {
    $(input).removeClass('is-invalid');
  } else {
    $(input).addClass('is-invalid');
  }
}

let currentUsername;

function validateUsername(fetchedCurrentUsername) {
  currentUsername = fetchedCurrentUsername;
  const newUsername = $('#usernameInput').val().toLowerCase();
  const errorMessageContainer = $('#usernameInput').siblings('.invalid-feedback');

  $('#usernameInput').on('input', function () {
    // Remove spaces from the input value
    let inputValue = $(this).val().replace(/ /g, '');
    $(this).val(inputValue);
  });

  // If the new username is the same as the current username, remove any validation errors and return
  if (newUsername === currentUsername.toLowerCase()) {
    $('#usernameInput').removeClass('is-invalid');
    errorMessageContainer.text('');
    return;
  }

  // Check if username contains space
  if (/\s/.test(newUsername)) {
    $('#usernameInput').addClass('is-invalid');
    errorMessageContainer
      .text('Username cannot contain spaces')
      .addClass('error-message');
  } else if (newUsername.length >= 4 && newUsername.length <= 25) {
    // Convert username to lowercase before sending AJAX request
    $.post('/check_username', { username: newUsername }, function (data) {
      if (data.username_exists && newUsername !== currentUsername.toLowerCase()) {
        $('#usernameInput').addClass('is-invalid');
        errorMessageContainer
          .text('Username is already taken')
          .addClass('error-message');
      } else {
        $('#usernameInput').removeClass('is-invalid');
        errorMessageContainer.text('');
      }
    });
  } else {
    $('#usernameInput').addClass('is-invalid');
    if (newUsername.length === 0) {
      errorMessageContainer
        .text('Username is required')
        .addClass('error-message');
    } else {
      errorMessageContainer
        .text('Username must be between 4 and 25 characters')
        .addClass('error-message');
    }
  }
}

function validateCurrentPassword() {
  const currentPassword = $('#currentPasswordInput').val();
  const currentPasswordErrorMessage = $('#currentPasswordInput').siblings('.invalid-feedback');
  const saveChangesBtn = $('#saveChangesBtn');

  if (currentPassword.length === 0) {
    $('#currentPasswordInput').addClass('is-invalid');
    currentPasswordErrorMessage.text('Please enter your current password.');
    saveChangesBtn.prop('disabled', true); // Disable the "Save Changes" button
  } else {
    $('#currentPasswordInput').removeClass('is-invalid');
    currentPasswordErrorMessage.text('');
    saveChangesBtn.prop('disabled', false); // Enable the "Save Changes" button
  }
}

function validateNewPassword() {
  const newPassword = $('#newPasswordInput').val();
  const newPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$/;
  const newPasswordErrorMessage = $('#newPasswordInput').siblings('.invalid-feedback');

  if (!newPasswordRegex.test(newPassword)) {
    $('#newPasswordInput').addClass('is-invalid');
    newPasswordErrorMessage.text('Password must be at least 6 characters long, contain at least one uppercase letter, one lowercase letter, one digit, and one special character.');
  } else {
    $('#newPasswordInput').removeClass('is-invalid');
    newPasswordErrorMessage.text('');
  }
}

function fetchCurrentUserData() {
  $.ajax({
    url: '/get_current_user',
    type: 'GET',
    success: function (data) {
      if (data.error) {
        console.error('Error fetching current user data:', data.error);
      } else {
        const fetchedCurrentUsername = data.username;
        // Use the fetchedCurrentUsername value in your validation logic
        validateUsername(fetchedCurrentUsername);
      }
    },
    error: function (xhr, status, error) {
      console.error('Error fetching current user data:', error);
    }
  });
}