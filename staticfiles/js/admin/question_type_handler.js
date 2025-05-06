document.addEventListener('DOMContentLoaded', function() { 
    const typeSelector = document.querySelector('#id_question_type');
    
    if (!typeSelector) {
        console.warn('No element with ID "id_question_type" found. Skipping field toggling.');
        return;  // Անթարվում է առցանց կապի հետ գործողության շարունակումը
    }
    
    const multipleChoiceField = document.querySelector('#id_multiple_choices');
    const openTextField = document.querySelector('#id_open_text_prompt');
    const ratingFields = document.querySelectorAll('#id_scale_min, #id_scale_max');
    
    function toggleFields() {
        console.log('JS file loaded');
        const selectedType = typeSelector.value;
        const yesNoOptions = JSON.stringify([{"text": "Այո", "value": 1}, {"text": "Ոչ", "value": 0}]);
        console.log(yesNoOptions);
 

        if (multipleChoiceField) {
            multipleChoiceField.disabled = false;
        }
        if (openTextField) {
            openTextField.disabled = false;
        }
        if (ratingFields) {
            ratingFields.forEach(field => field.disabled = false);
        }

        switch(selectedType) {
            case 'yes_no':
                if (multipleChoiceField) {
                    multipleChoiceField.value = yesNoOptions;
                    multipleChoiceField.disabled = true;
                }
                if (openTextField) {
                    openTextField.value = '';
                    openTextField.disabled = true;
                }
                if (ratingFields) {
                    ratingFields.forEach(field => {
                        field.value = '';
                        field.disabled = true;
                    });
                }
                break;
                
            case 'multiple_choice':
                if (openTextField) {
                    openTextField.value = '';
                    openTextField.disabled = true;
                }
                if (ratingFields) {
                    ratingFields.forEach(field => {
                        field.value = '';
                        field.disabled = true;
                    });
                }
                break;
                
            case 'open_text':
                if (multipleChoiceField) {
                    multipleChoiceField.value = '';
                    multipleChoiceField.disabled = true;
                }
                if (ratingFields) {
                    ratingFields.forEach(field => {
                        field.value = '';
                        field.disabled = true;
                    });
                }
                break;
                
            case 'rating_scale':
                if (multipleChoiceField) {
                    multipleChoiceField.value = '';
                    multipleChoiceField.disabled = true;
                }
                if (openTextField) {
                    openTextField.value = '';
                    openTextField.disabled = true;
                }
                if (ratingFields) {
                    ratingFields.forEach(field => {
                        if (!field.value.trim()) {
                            field.value = field.id === 'id_scale_min' ? 1 : 10;
                        }
                    });
                }
                break;
        }
    }
     
    typeSelector.addEventListener('change', toggleFields);
    toggleFields();
});
