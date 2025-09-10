document.addEventListener("DOMContentLoaded", function () {
    const fieldType = document.getElementById("id_field_type");
    const optionsRow = document.querySelector(".form-row.field-options"); 

    function toggleOptions() {
        if (fieldType.value === "select") {
            optionsRow.style.display = "block";
        } else {
            optionsRow.style.display = "none";
        }
    }

    if (fieldType && optionsRow) {
        toggleOptions();  // initial load
        fieldType.addEventListener("change", toggleOptions);
    }
});
