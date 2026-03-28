import os
import random
import time

from locust import HttpUser, LoadTestShape, between, task


API_KEY = os.getenv("API_KEY", "concessionaria-api-key-2026")
API_HEADER = os.getenv("API_HEADER", "x-api-key")


class ClienteUser(HttpUser):
	"""
	Fluxo principal do teste:
	1) Cria cliente via POST /clientes/novo
	2) Le cliente criado via GET /clientes/{id}
	"""

	wait_time = between(0.1, 0.8)

	def on_start(self):
		self.headers = {
			"Content-Type": "application/json",
			API_HEADER: API_KEY,
		}

	def _cpf_11_digitos(self) -> str:
		# Gera CPF unico para evitar colisao no campo unique.
		base = str(int(time.time() * 1000))[-7:]
		sufixo = f"{random.randint(0, 9999):04d}"
		return f"{base}{sufixo}"

	def _payload_cliente(self) -> dict:
		sufixo = random.randint(10000, 99999)
		return {
			"nome": f"Cliente Locust {sufixo}",
			"cpf": self._cpf_11_digitos(),
			"telefone": "11999990000",
			"email": f"locust{sufixo}@teste.com",
			"endereco": "Rua Teste, 123",
		}

	@task
	def criar_e_ler_cliente(self):
		payload = self._payload_cliente()

		with self.client.post(
			"/clientes/novo",
			json=payload,
			headers=self.headers,
			name="POST /clientes/novo",
			catch_response=True,
		) as post_resp:
			if post_resp.status_code != 201:
				post_resp.failure(
					f"POST falhou: status={post_resp.status_code}, body={post_resp.text}"
				)
				return

			try:
				body = post_resp.json()
			except Exception:
				post_resp.failure("POST retornou payload invalido (nao JSON).")
				return

			cliente_id = body.get("id")
			if not cliente_id:
				post_resp.failure("POST nao retornou campo id.")
				return

			post_resp.success()

		with self.client.get(
			f"/clientes/{cliente_id}",
			headers=self.headers,
			name="GET /clientes/{id}",
			catch_response=True,
		) as get_resp:
			if get_resp.status_code != 200:
				get_resp.failure(
					f"GET falhou: status={get_resp.status_code}, body={get_resp.text}"
				)
				return

			try:
				body = get_resp.json()
			except Exception:
				get_resp.failure("GET retornou payload invalido (nao JSON).")
				return

			if body.get("id") != cliente_id:
				get_resp.failure(
					f"GET retornou id diferente. Esperado={cliente_id}, obtido={body.get('id')}"
				)
				return

			get_resp.success()


class CargaCrescenteShape(LoadTestShape):
	"""
	Carga crescente por estagios (users, spawn_rate, duracao_em_segundos):
	- (10, 2, 120)
	- (30, 5, 120)
	- (60, 10, 120)
	- (100, 15, 120)
	"""

	stages = [
		{"duration": 120, "users": 10, "spawn_rate": 2},
		{"duration": 240, "users": 30, "spawn_rate": 5},
		{"duration": 360, "users": 60, "spawn_rate": 10},
		{"duration": 480, "users": 100, "spawn_rate": 15},
	]

	def tick(self):
		run_time = self.get_run_time()

		for stage in self.stages:
			if run_time < stage["duration"]:
				return stage["users"], stage["spawn_rate"]

		# Encerra o teste apos o ultimo estagio.
		return None
