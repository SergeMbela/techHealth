import numpy as np
a= np.zeros(10, dtype=int)
print(a)


b = np.ones((10, 14), dtype=float)
print(b)


c = np.arange(12).reshape(3, 4)
print(c)


#d'une moyenne de 0 et d'écart type de 1
d = np.random.normal(0,1, (3,3))
print(d)


#x

f= np.random.randint(10, size=6)
print(f)

g= np.random.randint(10, size=(3,4,5))
print(g)
print(g.itemsize)
print(g.size)


# On compte à partir de - 1 pour compter vers le bas
print ('On compte à partir de - 1 pour compter vers le bas')
mat = np.array([range(i,i+3) for i in [1,4,7]])
print (mat)
print (mat[-1,1])


# Create liste
liste = list(range(10))
print(liste)
# Create array
listV1 = np.arange(0,10)
print(listV1)
# Create array
listV2 = np.arange(0,10)
print(listV2)



# 3. Element après 5
print('Element après 5')
print(listV2[6::1])
idx = np.where(listV2 == 5)[0][0]
print(idx)
print(listV2[idx::1])

# 4. Récuperer les 4 éléments de 4 à 7
try:
    print('Récupérer les 4 éléments de 4 à 7')
    idx = np.where(listV2 == 4)[0][0]
    idy = np.where(listV2 == 7)[0][0] + 1
    print(listV2[idx:idy])  # Affiche [4 5 6 7]
except IndexError as e:
    print(f"❌ Valeur non trouvée dans la liste : {e}")



# 5. Create array (nombre pair)
print('# 5. Create array (nombre pair)')
print(listV2[0::2])

# 6.Create array (impair)
print(listV2[1::2])

# 7.Trois derniers éléments
print(listV2[-3:])

# 8.Elements par ordre inverse
print(listV2[::-1])

# 9.5 premiers en ordre inverse
print(listV2[4::-1])


######################


# De 0 à 9 (exclu)
array_id = np.arange(9,0,-1)
print(array_id)
# Résultat : [0 1 2 3 4 5 6 7 8 9]

# De 5 à 15
array_id = np.arange(5, 15)
print(array_id)
# Résultat : [ 5  6  7  8  9 10 11]()

print('Créer un tableau de 0 à 11 (12 éléments)')
# Créer un tableau de 0 à 11 (12 éléments)
array = np.arange(12)
print(array)
# [ 0  1  2  3  4  5  6  7  8  9 10 11]

# Le transformer en matrice 3x4
reshaped = array.reshape(3, 4)
print(reshaped)

print('1. Créer la matrice suivante')
v_list = [9,8,7,6,5,4,3,2,1]
print( v_list)
# Conversion en tableau 3x3
tableau = [v_list[i:i+3] for i in range(0, len(v_list), 3)]
# Affichage
for ligne in tableau:
    print(ligne)
    
print('2.Récuperer les sous matrices suivantes')
print('2.1 Récuperer les sous matrices suivantes')
tableau = [v_list[i:i+3:3] for i in range(0, len(v_list), 3)]
# Affichage
for ligne in tableau:
    print(ligne)
    
print('2.2 Récuperer les sous matrices suivantes')   
tableau = [v_list[i:i+2:1] for i in range(1, len(v_list), 3)]
# Affichage
for ligne in tableau:
    print(ligne)
    
print('2.3 Récuperer les sous matrices suivantes')   
tableau = [v_list[i:i+2:2] for i in range(1, len(v_list), 3)]
# Affichage
for ligne in tableau:
    print(ligne)
    
    
    
array_2d = np.array([range(i,i-3,-1) for i in [9,6,3]])
 
print("sous-matrices")
print(array_2d[:,0:1])
print(array_2d[:,0])
 
print(array_2d[:,1:])
print(array_2d[:2,:2])
 
print("inversion des lignes")
 
print(array_2d[::-1])



#Matrice
x1= np.arange(10,100,10).reshape ((3,3))
print(x1)

x2 = x1[1:,1:]
print(x2)

xs = x1[1,1]
print(xs)


x2 = x1[1:,1:].copy()
x2[0,0] =99
print(x2)

xs = x1[1,1]
print(xs)


# X
print ('Transposition')

x = [1,2,3]
y = [3,2,1]
print (np.concatenate([x,y],axis=0))


x = [[1,2,3]]
y = [[3,2,1]]
print (np.concatenate([x,y],axis=0))

x = [[1,2,3]]
y = [[3,2,1]]
print (np.concatenate([x,y],axis=1))

grid = [[1,2,3], [4,5,6]]
grid = np.concatenate([grid,grid],axis=0)
print(grid)

grid = np.concatenate([grid,grid],axis=1)
print(grid)


