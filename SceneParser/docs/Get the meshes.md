# How to get the meshes
Getting the bones to the textures and the mesh linked ain't easy.

Luckily for us, sometime they have the same name between a scene and a spritesheet.

If not:
 - Find the `MonoBehaviour` of the `GameObject` you want to map, for instance `image_hF_lthigh`.
   It should have a `m_SpriteMesh` with a **guid**. Copy it.
 - Go to every place where you have `.asset.meta` files in your game and search for the GUID.
   You should find something like `image_hasumiTfront_22.asset.meta`. Your image linked to the `image_hF_lthigh` is the `image_hasumiTfront_22`