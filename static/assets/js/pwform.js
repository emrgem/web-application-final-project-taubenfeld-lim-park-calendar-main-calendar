const add_single = document.querySelector('.add-individual')
const upload_cycle = document.querySelector('.upload-cycle')
const add_single_form = document.querySelector('.form-add-individual')
const upload_cycle_form = document.querySelector('.form-upload-cycle')

function show_add(e){
    add_single_form.style.display = 'block'
    upload_cycle_form.style.display = 'none'
    add_single.style.textDecoration = 'underline'
    upload_cycle.style.textDecoration = 'none'
}

function show_upload(e){
    add_single_form.style.display = 'none'
    upload_cycle_form.style.display = 'block'
    add_single.style.textDecoration = 'none'
    upload_cycle.style.textDecoration = 'underline'
}

add_single.addEventListener("click", show_add)
upload_cycle.addEventListener("click", show_upload)