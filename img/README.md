# hablai-img

pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu130
pip install transformers psycopg2-binary tqdm python-dotenv
pip install diffusers accelerate safetensors xformers peft


python generate_cards_from_db.py \
  --lora /home/ol/nvme512/models/lora/flat_cute_illustration.safetensors \
  --num-steps 20 \
  --guidance-scale 7.5 \
  --seed 42


генерирует полное говно. Пока оставим картинки