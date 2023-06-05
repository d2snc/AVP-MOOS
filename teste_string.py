import re

# String fornecida
string_pts = "pts={-2340,2370:-2340,2700},label=lancha_waypt_survey,label_color=invisible,edge_color=black,vertex_color=gray40,vertex_size=5,edge_size=1}"

# Extrair as coordenadas dos pontos usando expressões regulares
pattern = r'(-?\d+),(-?\d+)'
matches = re.findall(pattern, string_pts)

# Armazenar as coordenadas em uma lista de pontos
pontos = []
for match in matches:
    x = int(match[0])
    y = int(match[1])
    pontos.append((x, y))

# Exibir os pontos
print(pontos)