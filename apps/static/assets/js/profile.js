$(document).ready(function () {
  let currentUsername;
  let successMessageTimeout;

  fetchCurrentUserData();

  function showSuccessMessage() {
    // Clear any existing success message and timeout
    $('.alert-success').remove();
    if (successMessageTimeout) {
      clearTimeout(successMessageTimeout);
    }
  
    let successMessage = $('<div class="alert alert-success text-white" role="alert">Changes saved successfully!</div>');
    $('.modal-body').prepend(successMessage);
    
    // Set a timeout to remove the success message after 2 seconds
    successMessageTimeout = setTimeout(function() {
      successMessage.remove();
      // Force a repaint to ensure the removal is visually updated
      $('.modal-body')[0].offsetHeight;
      successMessageTimeout = null; // Clear the timeout variable
    }, 2000); // Changed to 2 seconds for better visibility
  }

  $('#editProfileBtn').click(function () {
    enableEditMode();
  });

  $('#saveChangesBtn').click(function (e) {
    e.preventDefault();
    console.log("Save Changes button clicked");

    let isValid = validateForm();

    if (isValid) {
      $('#profileForm').submit();
    }
  });


  $('#profileForm').on('submit', function (e) {
    e.preventDefault();

    $.ajax({
      url: $(this).attr('action'),
      type: 'POST',
      data: $(this).serialize(),
      success: function (response) {
        disableEditMode();
        showSuccessMessage();
        fetchCurrentUserData();
      },
      error: function (xhr, status, error) {
        console.error('Error updating profile:', error);
        alert('An error occurred while updating your profile. Please try again.');
      }
    });
  });

  $('#profileModal').on('hidden.bs.modal', function () {
    resetModalState();
  });

  $('#profileModal').on('show.bs.modal', function () {
    fetchCurrentUserData();
    resetModalState();
  });

  // Handle close button click
  $('#profileModal .close, #profileModal [data-dismiss="modal"]').on('click', function () {
    resetModalState();
  });
});

function enableEditMode() {
  $('#usernameInput, #currentPasswordInput, #newPasswordInput, #saveChangesBtn').removeAttr('disabled');
  $('#saveChangesBtn').show();
  $('#editProfileBtn').hide();

  $('#profileForm input').on('input', function () {
    validateInput(this);
  });

  $('#usernameInput').on('input', function () {
    validateUsername(currentUsername);
  });

  $('#currentPasswordInput').on('input', validateCurrentPassword);
  $('#newPasswordInput').on('input', validateNewPassword);
}

function disableEditMode() {
  $('#usernameInput, #currentPasswordInput, #newPasswordInput').attr('disabled', 'disabled');
  $('#saveChangesBtn').hide();
  $('#editProfileBtn').show();
}


function resetModalState() {
  disableEditMode();
  $('input.form-control').removeClass('is-invalid');
  $('.invalid-feedback').text('');
  $('#currentPasswordInput, #newPasswordInput').val('');
  $('.alert-success').remove();
  if (successMessageTimeout) {
    clearTimeout(successMessageTimeout);
    successMessageTimeout = null;
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
        $('#usernameInput').val(data.username);
        $('#emailInput').val(data.email);
        validateUsername(currentUsername);
      }
    },
    error: function (xhr, status, error) {
      console.error('Error fetching current user data:', error);
    }
  });
}

//VALIDATE FUNCTIONS
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

  if (newPassword.length === 0) {
    $('#newPasswordInput').removeClass('is-invalid');
    newPasswordErrorMessage.text('');
  } else if (!newPasswordRegex.test(newPassword)) {
    $('#newPasswordInput').addClass('is-invalid');
    newPasswordErrorMessage.text('Password must be at least 6 characters long, contain at least one uppercase letter, one lowercase letter, one digit, and one special character.');
  } else {
    $('#newPasswordInput').removeClass('is-invalid');
    newPasswordErrorMessage.text('');
  }
}

function validateForm() {
  let isValid = true;

  if ($('#usernameInput').hasClass('is-invalid')) {
    isValid = false;
  }

  if ($('#newPasswordInput').val() && $('#newPasswordInput').hasClass('is-invalid')) {
    isValid = false;
  }

  if (!$('#currentPasswordInput').val()) {
    $('#currentPasswordInput').addClass('is-invalid');
    isValid = false;
  } else {
    $('#currentPasswordInput').removeClass('is-invalid');
  }

  return isValid;
}