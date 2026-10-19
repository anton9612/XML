from django.shortcuts import render, redirect
from .forms import RecipeForm, XmlUploadForm
import xml.etree.ElementTree as ET
from django.conf import settings

def read_xml(file_path):
    tree=ET.parse(file_path)
    root=tree.getroot()
    recipe_data={}
    for child in root:
        recipe_data[child.tag]=child.text or ""
    return recipe_data



def save_xml(recipe):
    root=ET.Element("recipe")
    for field_name, value in recipe.items():
        child=ET.SubElement(root,field_name)
        child.text=str(value)
    tree=ET.ElementTree(root)
    data_dir=settings.BASE_DIR/"recipes_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    index=1
    while (data_dir/f"recipe_{index}.xml").exists():
        index+=1
    filename=f"recipe_{index}.xml"
    file_path=data_dir/filename

    tree.write(
        file_path,
        encoding="utf-8",
        xml_declaration=True,
    )
    return filename

def validate_xml_file(file_path):
    tree=ET.parse(file_path)
    root=tree.getroot()
    if root.tag!="recipe":
        raise ValueError("Элемент должен называться recipe")
    data={}
    for child in root:
        data[child.tag]=child.text or ""
    required_fields=[
        "title",
        "cuisine",
        "cooking_time",
        "servings",
        "ingredients",
        "instructions",
        ]
    missing = [
        field for field in required_fields
        if field not in data
    ]
    if missing:
        raise ValueError("В XML отсутствуют поля: " + ", ".join(missing))
    try:
        cooking_time = int(data["cooking_time"])
        servings = int(data["servings"])
    except ValueError:
        raise ValueError("Время приготовления и количество порций должны быть целыми числами.") from None

def xml_upload(request):
    if request.method!="POST":
        return redirect("index")

    upload_form = XmlUploadForm(request.POST, request.FILES)
    if upload_form.is_valid():
        uploaded_file=upload_form.cleaned_data["xml_file"]
        data_dir = settings.BASE_DIR / "recipes_data"
        data_dir.mkdir(parents=True, exist_ok=True)

        index = 1
        file_path = data_dir / f"recipe_{index}.xml"

        while file_path.exists():
            index += 1
            file_path = data_dir / f"recipe_{index}.xml"

        with file_path.open("wb") as file:
            for chunk in uploaded_file.chunks():
                file.write(chunk)
        try:
            validate_xml_file(file_path)
        except(ET.ParseError, ValueError) as error:
            file_path.unlink(missing_ok=True)
            upload_form.add_error(
            "xml_file",
            f"Файл не прошёл проверку: {error}",)
        else:
            return redirect('index')
            
        data_dir = settings.BASE_DIR / "recipes_data"
        xml_recipes = []

        if data_dir.exists():
            for file_path in sorted(data_dir.glob("recipe_*.xml")):
                saved_recipe = read_xml(file_path)
                saved_recipe["filename"] = file_path.name
                xml_recipes.append(saved_recipe)

        context = {
            "form": RecipeForm(),
            "recipe": None,
            "xml_filename": None,
            "xml_recipes": xml_recipes,
            "upload_form": upload_form,
        }

        return render(request, "main/index.html", context)



def recipe_create(request):
    saved_recipe=None
    recipe=None
    xml_filename=None
    if request.method=="POST":
        form=RecipeForm(request.POST)
        if form.is_valid():
            recipe=form.cleaned_data
            xml_filename=save_xml(recipe)
            return redirect("index")
    if request.method=="GET":
        form=RecipeForm()
    data_dir=settings.BASE_DIR/"recipes_data"
    xml_recipes=[]
    if data_dir.exists():
        for file_path in data_dir.glob("recipe_*.xml"):
            saved_recipe=read_xml(file_path)
            saved_recipe["filename"]=file_path.name
            xml_recipes.append(saved_recipe)
    
    context={"form":form, "recipe":recipe, "xml_filename":xml_filename, "xml_recipes":xml_recipes, "upload_form": XmlUploadForm(),}

    return render(request,'main/index.html',context)