$(document).ready(function () {
  let currentUsername;

  fetchCurrentUserData();

  $('#editProfileBtn').click(function () {
    $('#usernameInput, #currentPasswordInput, #newPasswordInput, #saveChangesBtn').removeAttr('disabled');
    $('#saveChangesBtn').show();
    $(this).hide();

    $('#profileForm input').on('input', function () {
      validateInput(this);
    });

    $('#usernameInput').on('input', function () {
      validateUsername(currentUsername);
    });

    $('#currentPasswordInput').on('input', validateCurrentPassword);
    $('#newPasswordInput').on('input', validateNewPassword);
  });

  var profileModal = new bootstrap.Modal(document.getElementById('profileModal'), {
    backdrop: 'static',
    keyboard: false
  });
  
  var confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'), {
    backdrop: 'static',
    keyboard: false
  });

  // Handle Save Changes button click
  $('#saveChangesBtn').click(function(e) {
    e.preventDefault();
    console.log("Save Changes button clicked");

    let isValid = validateForm(); // Implement this function to check form validity

    if (isValid) {
      profileModal.hide();
      setTimeout(function() {
        confirmationModal.show();
      }, 300);
    }
  });

  // Handle Confirm Save Changes button click
  $('#confirmSaveChanges').click(function() {
    $.ajax({
      url: '/check_current_password',
      type: 'POST',
      data: { current_password: $('#currentPasswordInput').val() },
      success: function (data) {
        if (data.is_valid) {
          $('#profileForm').submit();
          $('#confirmationModal').modal('hide');
          $('#saveChangesModal').modal('show');
        } else {
          const currentPasswordErrorMessage = $('#currentPasswordInput').siblings('.invalid-feedback');
          currentPasswordErrorMessage.text('Incorrect current password.');
          $('#currentPasswordInput').addClass('is-invalid');
          $('#confirmationModal').modal('hide');
        }
      },
      error: function (xhr, status, error) {
        console.error('Error checking current password:', error);
        $('#confirmationModal').modal('hide');
      }
    });
  });

  $('#profileModal').on('hidden.bs.modal', function () {
    $('input.form-control').removeClass('is-invalid');
    $('.invalid-feedback').text('');
    $('#usernameInput').val(currentUsername.trim());
    $('#currentPasswordInput, #newPasswordInput').val('');
    $('#saveChangesBtn').hide();
    $('#editProfileBtn').show();
    $('#usernameInput, #currentPasswordInput, #newPasswordInput').attr('disabled', 'disabled');
  });

  $('#profileModal').on('show.bs.modal', fetchCurrentUserData);
});

function validateInput(input) {
  if (input.checkValidity()) {
    $(input).removeClass('is-invalid');
  } else {
    $(input).addClass('is-invalid');
  }
}

function validateUsername(fetchedCurrentUsername) {
  currentUsername = fetchedCurrentUsername;
  const newUsername = $('#usernameInput').val().toLowerCase();
  const errorMessageContainer = $('#usernameInput').siblings('.invalid-feedback');

  $('#usernameInput').val($('#usernameInput').val().replace(/ /g, ''));

  if (newUsername === currentUsername.toLowerCase()) {
    $('#usernameInput').removeClass('is-invalid');
    errorMessageContainer.text('');
    return;
  }

  if (/\s/.test(newUsername)) {
    $('#usernameInput').addClass('is-invalid');
    errorMessageContainer.text('Username cannot contain spaces').addClass('error-message');
  } else if (newUsername.length >= 4 && newUsername.length <= 25) {
    $.post('/check_username', { username: newUsername }, function (data) {
      if (data.username_exists && newUsername !== currentUsername.toLowerCase()) {
        $('#usernameInput').addClass('is-invalid');
        errorMessageContainer.text('Username is already taken').addClass('error-message');
      } else {
        $('#usernameInput').removeClass('is-invalid');
        errorMessageContainer.text('');
      }
    });
  } else {
    $('#usernameInput').addClass('is-invalid');
    errorMessageContainer.text(newUsername.length === 0 ? 'Username is required' : 'Username must be between 4 and 25 characters').addClass('error-message');
  }
}

function validateCurrentPassword() {
  const currentPassword = $('#currentPasswordInput').val();
  const currentPasswordErrorMessage = $('#currentPasswordInput').siblings('.invalid-feedback');
  const saveChangesBtn = $('#saveChangesBtn');

  if (currentPassword.length === 0) {
    $('#currentPasswordInput').addClass('is-invalid');
    currentPasswordErrorMessage.text('Please enter your current password.');
    saveChangesBtn.prop('disabled', true);
  } else {
    $('#currentPasswordInput').removeClass('is-invalid');
    currentPasswordErrorMessage.text('');
    saveChangesBtn.prop('disabled', false);
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
        currentUsername = data.username;
        validateUsername(currentUsername);
      }
    },
    error: function (xhr, status, error) {
      console.error('Error fetching current user data:', error);
    }
  });
}