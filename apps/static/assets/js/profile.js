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
    successMessageTimeout = setTimeout(function () {
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
      dataType: 'json',
      success: function (response) {
        console.log('Server response:', response);
        if (response.success) {
          console.log('Profile updated successfully');
          disableEditMode();
          showSuccessMessage();
          fetchCurrentUserData();

          // Clear password fields
          $('#currentPasswordInput').val('');
          $('#newPasswordInput').val('');
        } else {
          console.log('Error:', response.error);
          if (response.error === 'incorrect_password') {
            $('#currentPasswordInput').addClass('is-invalid');
            $('#currentPasswordInput').siblings('.invalid-feedback').text('Incorrect password');
          } else if (response.error === 'same_password') {
            $('#newPasswordInput').addClass('is-invalid');
            $('#newPasswordInput').siblings('.invalid-feedback').text('New password cannot be the same as the current password');
          } else {
            alert(response.message || 'An unexpected error occurred. Please try again.');
          }
        }
      },
      error: function (xhr, status, error) {
        console.error('Error updating profile:', error);
        console.log('XHR status:', status);
        console.log('XHR response:', xhr.responseText);
        try {
          var response = JSON.parse(xhr.responseText);
          if (response.error === 'incorrect_password') {
            $('#currentPasswordInput').addClass('is-invalid');
            $('#currentPasswordInput').siblings('.invalid-feedback').text('Incorrect password');
          } else if (response.error === 'same_password') {
            $('#newPasswordInput').addClass('is-invalid');
            $('#newPasswordInput').siblings('.invalid-feedback').text('New password cannot be the same as the current password');
          } else {
            alert(response.message || 'An error occurred while updating your profile. Please try again.');
          }
        } catch (e) {
          alert('An error occurred while updating your profile. Please try again.');
        }
      }
    });
  });

  let keepEditState = false;

  function hasUnsavedChanges() {
    return $('#usernameInput').val() !== currentUsername ||
      $('#currentPasswordInput').val() !== '' ||
      $('#newPasswordInput').val() !== '';
  }


  function showUnsavedChangesAlert() {
    return Swal.fire({
      title: 'Unsaved Changes',
      text: 'You have unsaved changes. Are you sure you want to close without saving?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      confirmButtonText: 'Yes, close',
      cancelButtonText: 'No, keep editing'
    }).then((result) => {
      return result.isConfirmed;
    });
  }

  $('#profileModal').on('hide.bs.modal', function (e) {
    if (hasUnsavedChanges()) {
      e.preventDefault();
      showUnsavedChangesAlert().then((shouldClose) => {
        if (shouldClose) {
          keepEditState = false;
          resetModalState();
          $('#profileModal').modal('hide');
        } else {
          keepEditState = true;
          $('#profileModal').modal('show');
        }
      });
    } else {
      keepEditState = false;
      resetModalState();
    }
  });

  $('#profileModal .close, #profileModal [data-dismiss="modal"]').on('click', function (e) {
    e.preventDefault();
    if (hasUnsavedChanges()) {
      showUnsavedChangesAlert().then((shouldClose) => {
        if (shouldClose) {
          keepEditState = false;
          resetModalState();
          $('#profileModal').modal('hide');
        } else {
          keepEditState = true;
          $('#profileModal').modal('show');
        }
      });
    } else {
      keepEditState = false;
      resetModalState();
      $('#profileModal').modal('hide');
    }
  });

  $('#profileModal').on('show.bs.modal', function () {
    if (!keepEditState) {
      fetchCurrentUserData();
      resetModalState();
    }
    keepEditState = false;
  });

  function enableEditMode() {
    keepEditState = true;
    $('#usernameInput, #currentPasswordInput, #newPasswordInput, #saveChangesBtn').removeAttr('disabled');
    $('#saveChangesBtn').show();
    $('#editProfileBtn').hide();
    $('.eye-toggle').show(); // Show eye toggle icons

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
    $('.eye-toggle').hide(); // Hide eye toggle icons
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
    // Reset username to current username
    $('#usernameInput').val(currentUsername);
    $('.eye-toggle').hide();
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
          $('#usernameInput').val(currentUsername);
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
      $(input).siblings('.invalid-feedback').text('');
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
      errorMessageContainer.text('Username cannot contain spaces');
    } else if (newUsername.length >= 4 && newUsername.length <= 25) {
      $.post('/check_username', { username: newUsername }, function (data) {
        if (data.username_exists && newUsername !== currentUsername.toLowerCase()) {
          $('#usernameInput').addClass('is-invalid');
          errorMessageContainer.text('Username is already taken');
        } else {
          $('#usernameInput').removeClass('is-invalid');
          errorMessageContainer.text('');
        }
      });
    } else {
      $('#usernameInput').addClass('is-invalid');
      errorMessageContainer.text(newUsername.length === 0 ? 'Username is required' : 'Username must be between 4 and 25 characters');
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
});
