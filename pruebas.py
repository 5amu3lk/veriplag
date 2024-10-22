from spellchecker import SpellChecker

# Inicializar el corrector ortográfico para español
spell = SpellChecker(language='es')

def correct_text(text):
    # Separar el texto en palabras
    words = text.split()
    # Corregir cada palabra
    corrected_words = [spell.correction(word) for word in words]
    # Unir las palabras corregidas en un solo texto
    return ' '.join(corrected_words)

# Texto de prueba
text_to_correct = "En una ocazion, los estidiantes fueron al zologico. Ellos se emocionaron mucho al ver a los animaless."
corrected_text = correct_text(text_to_correct)

print("Texto Original:")
print(text_to_correct)
print("\nTexto Corregido:")
print(corrected_text)
