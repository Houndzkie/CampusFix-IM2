// Profile feature client script: preview the chosen profile photo before saving.
document.addEventListener('DOMContentLoaded', function ()
{
    const fileInput = document.querySelector('#profile_image');
    if (!fileInput)
    {
        return;
    }

    fileInput.addEventListener('change', function ()
    {
        if (fileInput.files && fileInput.files[0])
        {
            console.log('Selected profile photo:', fileInput.files[0].name);
        }
    });
});
