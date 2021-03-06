"""@package 2D-Sword-py
This code provides facilities to solve the
scattering problem in bidimensional cavities. 
"""

from scipy.spatial import Delaunay
from scipy.special import jn, jvp, hankel1, hankel2, h1vp, h2vp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Setting the rc parameters.
rcParams['text.usetex'] = True
rcParams['text.latex.preamble'] = r'\usepackage[charter]{mathdesign}'
rcParams['font.size'] = 10
#rcParams['axes.labelsize'] = '10'
#rcParams['xtick.labelsize'] = '10'
#rcParams['ytick.labelsize'] = '10'
rcParams['legend.numpoints'] = 3

class Dielectric:
	"""
	Class that encapsulates the data pertaining to a dielectric
	cavity. The form of the boundary, given in the implicit form
	\f$r(\theta)\f$, has to be given as a callable function. 
	Subclasses will define the particular geometry.

	We will also generate the Delaunay triangulation of the given 
	area as a function of the number of points given to the constructor.
	Subclasses will define the particular distribution of points.

	Methods:
		- 
		-

	Attributes:
		-
		-
	"""

def user_mod(value, modulo):
	return value-modulo*int(np.floor(value/modulo))

class homoCircle:
	"""
	Class that defines the geometry and refractive index distribution
	of the circular and homogeneous cavity.
	"""
	def __init__(self, N, k, nc, no, r0, M):
		self.N = N
		self.k = k
		self.nc = nc
		self.no = no
		self.potential = nc*nc-no*no
		self.r0 = r0
		self.Mmax = M
		self.meshDistribution(N)
		self.triangulate()
		self.plotMesh()

	def refIndex(self, r, theta):
		if r < self.r0:
			return nc
		else:
			return no

	def boundary(self,theta):
		return self.r0

	def meshDistribution(self, N):
		N = int(np.sqrt(N))
		self.points = np.zeros((0,2))
		theta = np.linspace(0.0,2.0*np.pi,N*N)
		for i in range(N*N):
			self.points = np.insert(self.points, len(self.points), [self.boundary(theta[i]), theta[i]], axis=0)

		for j in range(len(self.points)):
			r = self.points[j,0]
			theta = self.points[j,1]
			self.points[j,0] = r*np.cos(theta)
			self.points[j,1] = r*np.sin(theta)

		x = np.linspace(-1,1,N)
		y = np.linspace(-1,1,N)
		for k in range(N):
			for h in range(N):
				if np.sqrt(x[k]*x[k]+y[h]*y[h])< 1.0:
					self.points = np.insert(self.points, len(self.points), [x[k], y[h]], axis=0)


	def triangulate(self):
		self.triangulation =  Delaunay(self.points)

	def plotMesh(self):
		self.nTriangles = self.triangulation.simplices.shape[0]
		fig1 = plt.figure(figsize=(3,3))
		ax1 = fig1.add_subplot(111)
		ax1.axis('off')
		plt.triplot(self.points[:,0],self.points[:,1], self.triangulation.simplices.copy())
		plt.plot(self.points[:,0], self.points[:,1], 'o')
		

		# -- Compute areas
		self.areas = np.zeros((0))
		self.centerPoints = np.zeros((0,2))
		for i in range(self.nTriangles):
			# -- Areas
			a = np.linalg.norm(self.points[self.triangulation.simplices][i,0,:]-self.points[self.triangulation.simplices][i,1,:])
			b = np.linalg.norm(self.points[self.triangulation.simplices][i,1,:]-self.points[self.triangulation.simplices][i,2,:])
			c = np.linalg.norm(self.points[self.triangulation.simplices][i,2,:]-self.points[self.triangulation.simplices][i,0,:])
			s = (a+b+c)/2.0
			self.areas = np.insert(self.areas, len(self.areas),np.sqrt(s*(s-a)*(s-b)*(s-c)))
			
			# -- Center points
			a = np.linalg.norm(self.points[self.triangulation.simplices][i,0,:]-self.points[self.triangulation.simplices][i,1,:])
			b = np.linalg.norm(self.points[self.triangulation.simplices][i,1,:]-self.points[self.triangulation.simplices][i,2,:])
			c = np.linalg.norm(self.points[self.triangulation.simplices][i,2,:]-self.points[self.triangulation.simplices][i,0,:])
			x = 1/a
			z = 1/b
			y = 1/c
			sumXYZ = a*x+b*y+c*z
			alpha = a*x/sumXYZ
			beta = b*y/sumXYZ
			gamma = c*z/sumXYZ

			self.centerPoints = np.insert(self.centerPoints, len(self.centerPoints), 
				alpha*self.points[self.triangulation.simplices][i,0,:]
				+beta*self.points[self.triangulation.simplices][i,1,:]
				+gamma*self.points[self.triangulation.simplices][i,2,:], axis=0)

		plt.plot(self.centerPoints[:,0], self.centerPoints[:,1], 'ro')
		plt.savefig("meshCircle-%s.pdf" %(self.N))
		#plt.show()

	def computeScatteringMatrix(self,Mmax):
		# -- Prepare scattering matrix. 
		scatMat = np.zeros((2*Mmax+1,2*Mmax+1), dtype=np.complex)

		for n in range(2*Mmax+1):
			m = n-Mmax
			# -- Prepare the vector and matrix
			b = np.zeros((self.nTriangles), dtype=np.complex)
			M = np.zeros((self.nTriangles,self.nTriangles), dtype=np.complex)
	
			for i in range(self.nTriangles):
				b[i] = jn(m, self.k*np.linalg.norm(self.centerPoints[i]))*np.exp(1j*m*user_mod(np.arctan2(self.centerPoints[i,1],self.centerPoints[i,0]),2*np.pi))
	
				for j in range(self.nTriangles):
					if (i!=j):
						d = self.k*np.linalg.norm(self.centerPoints[i]-self.centerPoints[j])
						phi1 = user_mod(np.arctan2(self.centerPoints[i,1],self.centerPoints[i,0]),2*np.pi)
						phi2 = user_mod(np.arctan2(self.centerPoints[j,1],self.centerPoints[j,0]),2*np.pi)
						M[i,j] = self.potential*self.k*self.k*1j*hankel1(0, d)*self.areas[j]/4.0
	
			x = np.linalg.solve(np.eye(self.nTriangles,self.nTriangles, dtype=np.complex)-M,b)
			fig2 = plt.figure(figsize=(3,3))
			ax2 = fig2.add_subplot(111)
			ax2.axis('off')
			plt.tripcolor(self.points[:,0], self.points[:,1],self.triangulation.simplices, np.abs(x))
			plt.savefig("intensityTest-%s.pdf" %(self.N))
			

			# -- We compute the corresponding line of the scattering matrix.
			for k in range(2*Mmax+1):
				mp = k-Mmax
				Smm = 0.0
				for h in range(self.nTriangles):
					d = self.k*np.linalg.norm(self.centerPoints[h])
					phi = user_mod(np.arctan2(self.centerPoints[h,1],self.centerPoints[h,0]),2*np.pi)
					Smm += self.potential*jn(mp,d)*np.exp(-1j*mp*phi)*x[h]*self.areas[h]

				Smm = self.k*self.k*1j*Smm/2.0
				Smm += (1.0 if mp==m else 0.0)
				scatMat[k,n] = Smm

		return scatMat
	
	
if __name__ == '__main__':
	mesh = [25, 50, 100, 200, 300,500,1000,2000]
	convergence = np.zeros((0,2))
	for nPoints in mesh:
		y = homoCircle(nPoints, 1.0, 2.0, 1.0, 1.0, 1)
		scatMat = y.computeScatteringMatrix(y.Mmax)
	
		analScatMat = np.zeros(2*y.Mmax+1, dtype=complex)
		zc = y.nc*y.k
		zo = y.no*y.k
		eta = y.nc/y.no
		for i in range(2*y.Mmax+1):
			m = i-y.Mmax
			num = -(eta*jvp(m,zc)*hankel2(m,zo)-jn(m,zc)*h2vp(m,zo))
			den = eta*jvp(m,zc)*hankel1(m,zo)-jn(m,zc)*h1vp(m,zo)
			analScatMat[i] = num/den
		err = np.amax(np.abs(np.diag(analScatMat)-scatMat))
		print(err)
		print(analScatMat)

		# -- Mean areas of triangles
		convergence = np.insert(convergence, len(convergence), [np.mean(y.areas), err],axis=0)

	fig1 = plt.figure(figsize=(5,3))
	ax1 = fig1.add_subplot(111)
	plt.plot(convergence[:,0],convergence[:,1], ls='--', marker='o', label=r"Numerical Error")

	p = np.polyfit(np.log(convergence[:,0]),np.log(convergence[:,1]),1)
	ynew = np.exp(np.polyval(p,np.log(convergence[:,0])))
	plt.plot(convergence[:,0],ynew, label=r"Power-law fit: $\alpha=%0.2g$" %(p[0]))

	ax1.set_xscale('log')
	ax1.set_yscale('log')
	ax1.set_xlabel('Average area of triangles')
	ax1.set_ylabel("Absolute error on $S_{00}$")
	ax1.invert_xaxis()
	ax1.grid(True)
	ax1.legend(loc=0)
	print(p)
	plt.savefig("convergenceAnalysis.pdf", bbox_inches='tight')