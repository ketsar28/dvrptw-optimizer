"""
solver.py — Mesin Optimasi DVRPTW
===================================
Dynamic Vehicle Routing Problem with Time Windows.
Kombinasi algoritma: Nearest Neighbor Heuristic (solusi awal)
+ Cheapest Insertion (penyisipan pelanggan dinamis)
+ RVND (Randomized Variable Neighborhood Descent) untuk optimasi lokal.

Penulis  : Farida Nuha
Universitas Negeri Malang — Matematika

Batasan Model:
- 2 kendaraan homogen dengan kapasitas masing-masing 2500 kg
- Setiap rute berawal dan berakhir di depot (node 0)
- Setiap pelanggan hanya dilayani satu kali oleh satu kendaraan
- Non-preemption: kendaraan tidak bisa putar balik di tengah jalan
- Pelanggan dinamis disisipkan ke posisi layak setelah node yang sudah dikunjungi
"""

import copy
import random
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


# ─────────────────────────────────────────────────────────────
# STRUKTUR DATA
# ─────────────────────────────────────────────────────────────

@dataclass
class Customer:
    """Representasi satu node pelanggan dalam jaringan distribusi DVRPTW."""
    id: int
    demand: float
    service_time: float          # durasi pelayanan dalam jam desimal
    is_dynamic: bool = False     # True jika pelanggan muncul setelah operasi berjalan
    reveal_time: float = 0.0    # jam saat pesanan masuk ke sistem (0 = statis/diketahui sejak awal)
    time_window_open: float = 0.0
    time_window_close: float = 24.0


@dataclass
class Depot:
    """Konfigurasi depot pusat distribusi."""
    id: int = 0
    tw_open: float = 4.0         # jam buka depot (04:00)
    tw_close: float = 7.0        # jam tutup depot (07:00)
    capacity: int = 2500         # kapasitas TIAP kendaraan (bukan total gabungan)
    speed: float = 60.0          # kecepatan rata-rata kendaraan (km/jam)
    max_vehicles: int = 2        # jumlah kendaraan yang tersedia


@dataclass
class Route:
    """Satu rute kendaraan: urutan node dimulai dan diakhiri di depot (0)."""
    path: List[int] = field(default_factory=lambda: [0, 0])
    total_distance: float = 0.0
    total_time: float = 0.0
    total_load: float = 0.0

    @property
    def customers_only(self) -> List[int]:
        """Daftar ID pelanggan saja tanpa depot."""
        return [n for n in self.path if n != 0]

    @property
    def is_empty(self) -> bool:
        """Cek apakah rute kosong (tidak ada pelanggan)."""
        return len(self.customers_only) == 0


@dataclass
class SimulationState:
    """Cuplikan kondisi simulasi pada satu titik waktu tertentu."""
    current_time: float = 0.0
    routes: List[Route] = field(default_factory=list)
    visited: set = field(default_factory=set)
    committed: set = field(default_factory=set)
    pending_dynamic: List[int] = field(default_factory=list)
    active_customers: set = field(default_factory=set)


# ─────────────────────────────────────────────────────────────
# UTILITAS MATRIKS & METRIK RUTE
# ─────────────────────────────────────────────────────────────

def compute_distance_matrix(dist_input: np.ndarray) -> np.ndarray:
    """Konversi input matriks jarak ke format numpy array."""
    return np.array(dist_input, dtype=float)


def compute_time_matrix(time_input: np.ndarray) -> np.ndarray:
    """Konversi input matriks waktu tempuh ke format numpy array."""
    return np.array(time_input, dtype=float)


def route_distance(path: List[int], dist_mtx: np.ndarray) -> float:
    """Hitung total jarak satu rute berdasarkan urutan node."""
    return sum(dist_mtx[path[i]][path[i + 1]] for i in range(len(path) - 1))


def route_time(path: List[int], time_mtx: np.ndarray,
               customers: Dict[int, Customer]) -> float:
    """Hitung total waktu satu rute (perjalanan + pelayanan di setiap node)."""
    t = 0.0
    for i in range(len(path) - 1):
        t += time_mtx[path[i]][path[i + 1]]
        nxt = path[i + 1]
        if nxt != 0 and nxt in customers:
            t += customers[nxt].service_time
    return t


def get_route_arrival_times(path: List[int], time_mtx: np.ndarray,
                            customers: Dict[int, Customer], tw_open: float) -> List[float]:
    """
    Hitung daftar waktu kedatangan kendaraan di setiap node dalam rute.
    Digunakan untuk menentukan batas committed (node yang sudah dilalui).
    """
    arrival_times = [tw_open]
    t = tw_open
    for i in range(len(path) - 1):
        t += time_mtx[path[i]][path[i + 1]]
        arrival_times.append(t)
        nxt = path[i + 1]
        if nxt != 0 and nxt in customers:
            t += customers[nxt].service_time
    return arrival_times


def total_distance(routes: List[Route], dist_mtx: np.ndarray) -> float:
    """Total jarak seluruh rute kendaraan."""
    return sum(route_distance(r.path, dist_mtx) for r in routes)


def total_time(routes: List[Route], time_mtx: np.ndarray,
               customers: Dict[int, Customer]) -> float:
    """Total waktu operasional seluruh rute kendaraan."""
    return sum(route_time(r.path, time_mtx, customers) for r in routes)


def update_route_metrics(route: Route, dist_mtx: np.ndarray,
                         time_mtx: np.ndarray,
                         customers: Dict[int, Customer]) -> Route:
    """Rekalkulasi metrik rute (jarak, waktu, muatan) setelah perubahan path."""
    route.total_distance = route_distance(route.path, dist_mtx)
    route.total_time = route_time(route.path, time_mtx, customers)
    route.total_load = sum(
        customers[n].demand for n in route.customers_only if n in customers
    )
    return route


# ─────────────────────────────────────────────────────────────
# PENGECEKAN KELAYAKAN RUTE (FEASIBILITY)
# ─────────────────────────────────────────────────────────────

def is_route_feasible(path: List[int], time_mtx: np.ndarray,
                      customers: Dict[int, Customer],
                      depot: Depot) -> bool:
    """
    Cek apakah suatu rute layak secara teknis:
    - Akumulasi muatan <= kapasitas kendaraan (2500 kg per kendaraan)
    - Total waktu operasi <= durasi jam kerja depot
    """
    load = 0.0
    t = 0.0
    tw_limit = depot.tw_close - depot.tw_open

    for i in range(len(path) - 1):
        t += time_mtx[path[i]][path[i + 1]]
        nxt = path[i + 1]
        if nxt != 0 and nxt in customers:
            load += customers[nxt].demand
            t += customers[nxt].service_time

    return load <= depot.capacity and t <= tw_limit


# ─────────────────────────────────────────────────────────────
# NEAREST NEIGHBOR — KONSTRUKSI SOLUSI AWAL
# ─────────────────────────────────────────────────────────────

def nearest_neighbor(customer_ids: List[int],
                     dist_mtx: np.ndarray,
                     time_mtx: np.ndarray,
                     customers: Dict[int, Customer],
                     depot: Depot) -> List[Route]:
    """
    Konstruksi solusi awal menggunakan Nearest Neighbor Heuristic.
    Membangun rute satu per satu: mulai dari depot, kunjungi pelanggan
    terdekat yang masih layak (kapasitas & waktu), ulangi sampai semua dilayani.

    Jumlah rute dibatasi sesuai depot.max_vehicles (2 kendaraan).
    Jika kapasitas/waktu habis di satu rute, buka rute baru selama
    belum melebihi batas kendaraan.
    """
    unvisited = set(customer_ids)
    routes = []
    tw_limit = depot.tw_close - depot.tw_open

    while unvisited and len(routes) < depot.max_vehicles:
        path = [0]
        curr = 0
        load = 0.0
        t_used = 0.0

        # Pilih pelanggan terdekat dari depot sebagai titik awal rute
        first = min(unvisited, key=lambda c: dist_mtx[0][c])
        c_data = customers[first]

        # Cek kelayakan pelanggan pertama (demand + waktu pulang-pergi)
        t_check = time_mtx[0][first] + c_data.service_time + time_mtx[first][0]
        if c_data.demand > depot.capacity or t_check > tw_limit:
            unvisited.discard(first)
            continue

        path.append(first)
        unvisited.discard(first)
        load += c_data.demand
        t_used += time_mtx[0][first] + c_data.service_time
        curr = first

        # Tambahkan pelanggan berikutnya yang paling dekat dan masih layak
        while True:
            feasible = []
            for c in unvisited:
                cd = customers[c]
                new_load = load + cd.demand
                new_time = (t_used + time_mtx[curr][c]
                            + cd.service_time + time_mtx[c][0])
                if new_load <= depot.capacity and new_time <= tw_limit:
                    feasible.append(c)

            if not feasible:
                break

            next_node = min(feasible, key=lambda c: dist_mtx[curr][c])
            path.append(next_node)
            unvisited.discard(next_node)

            cd = customers[next_node]
            load += cd.demand
            t_used += time_mtx[curr][next_node] + cd.service_time
            curr = next_node

        path.append(0)  # kembali ke depot
        r = Route(path=path)
        r = update_route_metrics(r, dist_mtx, time_mtx, customers)
        routes.append(r)

    return routes


# ─────────────────────────────────────────────────────────────
# CHEAPEST INSERTION — PENYISIPAN PELANGGAN DINAMIS
# ─────────────────────────────────────────────────────────────

def cheapest_insertion(new_customer_id: int,
                       routes: List[Route],
                       dist_mtx: np.ndarray,
                       time_mtx: np.ndarray,
                       customers: Dict[int, Customer],
                       depot: Depot,
                       current_time: float) -> List[Route]:
    """
    Sisipkan pelanggan dinamis baru ke posisi paling murah (cheapest cost increase)
    di antara rute-rute yang sudah berjalan.

    Aturan Non-Preemption:
    - Hitung waktu kedatangan di tiap node rute untuk mengetahui node mana yang
      sudah terlanjur dikunjungi (committed) pada current_time.
    - Penyisipan HANYA boleh dilakukan SETELAH node terakhir yang committed.
    - Kendaraan tidak boleh putar balik; harus selesaikan titik sekarang dulu.

    Contoh Nuha: Rute awal 0-2-4-1-0, pelanggan dinamis 7 disisipkan
    menjadi 0-2-4-7-1-0 jika posisi antara 4 dan 1 paling murah.
    """
    best_cost = float("inf")
    best_route_idx = -1
    best_pos = -1

    for r_idx, route in enumerate(routes):
        old_dist = route.total_distance

        # Hitung waktu kedatangan di setiap node sepanjang rute ini
        arrival_times = get_route_arrival_times(
            route.path, time_mtx, customers, depot.tw_open
        )

        # Cari batas indeks node yang sudah committed (dilalui sebelum current_time)
        committed_boundary = 0
        for idx, arr_t in enumerate(arrival_times):
            if arr_t <= current_time:
                committed_boundary = idx

        # Posisi penyisipan hanya setelah committed_boundary (non-preemption)
        for pos in range(committed_boundary + 1, len(route.path)):
            new_path = route.path[:pos] + [new_customer_id] + route.path[pos:]

            # Cek kelayakan rute baru (kapasitas + waktu)
            if not is_route_feasible(new_path, time_mtx, customers, depot):
                continue

            new_dist = route_distance(new_path, dist_mtx)
            cost_increase = new_dist - old_dist

            if cost_increase < best_cost:
                best_cost = cost_increase
                best_route_idx = r_idx
                best_pos = pos

    if best_route_idx >= 0:
        # Sisipkan pelanggan di posisi terbaik yang ditemukan
        routes[best_route_idx].path.insert(best_pos, new_customer_id)
        routes[best_route_idx] = update_route_metrics(
            routes[best_route_idx], dist_mtx, time_mtx, customers
        )
    else:
        # Jika tidak muat di rute manapun, buat rute baru (jika kendaraan masih tersedia)
        new_path = [0, new_customer_id, 0]
        if is_route_feasible(new_path, time_mtx, customers, depot):
            r = Route(path=new_path)
            r = update_route_metrics(r, dist_mtx, time_mtx, customers)
            routes.append(r)

    return routes


# ─────────────────────────────────────────────────────────────
# PENCARIAN LOKAL — PERBAIKAN INTRA-RUTE (DALAM SATU RUTE)
# ─────────────────────────────────────────────────────────────

def get_committed_index(path: List[int], time_mtx: np.ndarray,
                        customers: Dict[int, Customer],
                        tw_open: float, current_time: float) -> int:
    """
    Mendapatkan indeks terakhir dalam path yang sudah committed
    (dikunjungi sebelum/pada current_time).
    Semua node sebelum indeks ini TIDAK boleh digeser/ditukar.
    """
    arrival_times = get_route_arrival_times(path, time_mtx, customers, tw_open)
    committed_idx = 0
    for idx, arr_t in enumerate(arrival_times):
        if arr_t <= current_time:
            committed_idx = idx
    return committed_idx


def two_opt_improve(route: Route, dist_mtx: np.ndarray,
                     time_mtx: np.ndarray,
                     customers: Dict[int, Customer],
                     depot: Depot,
                     current_time: float = 0.0) -> Tuple[Route, bool]:
    """
    Perbaikan 2-Opt intra-rute: balik urutan sub-segmen rute.
    Hanya mengubah bagian rute yang belum dikunjungi (uncommitted).
    """
    path = route.path
    best_path = path[:]
    best_dist = route.total_distance
    improved = False

    c_idx = get_committed_index(path, time_mtx, customers, depot.tw_open, current_time)

    # 2-opt hanya boleh menukar bagian rute setelah node committed
    start_pos = max(1, c_idx + 1)

    for i in range(start_pos, len(path) - 2):
        for j in range(i + 1, len(path) - 1):
            # Balik urutan segmen dari posisi i sampai j
            candidate = path[:i] + path[i:j + 1][::-1] + path[j + 1:]
            if not is_route_feasible(candidate, time_mtx, customers, depot):
                continue
            d = route_distance(candidate, dist_mtx)
            if d + 1e-9 < best_dist:
                best_dist = d
                best_path = candidate
                improved = True

    if improved:
        route.path = best_path
        route = update_route_metrics(route, dist_mtx, time_mtx, customers)
    return route, improved


def or_opt_improve(route: Route, dist_mtx: np.ndarray,
                   time_mtx: np.ndarray,
                   customers: Dict[int, Customer],
                   depot: Depot,
                   current_time: float = 0.0) -> Tuple[Route, bool]:
    """
    Or-Opt: pindahkan segmen 1 atau 2 node ke posisi lain dalam rute.
    Hanya mengubah bagian rute yang belum dikunjungi (uncommitted).
    """
    path = route.path
    best_path = path[:]
    best_dist = route.total_distance
    improved = False

    c_idx = get_committed_index(path, time_mtx, customers, depot.tw_open, current_time)
    start_pos = max(1, c_idx + 1)

    for seg_len in [1, 2]:
        for i in range(start_pos, len(path) - 1 - seg_len + 1):
            seg = path[i:i + seg_len]
            base = path[:i] + path[i + seg_len:]

            # Cari posisi penempatan baru yang juga di belakang committed node
            base_c_idx = get_committed_index(
                base, time_mtx, customers, depot.tw_open, current_time
            )
            insert_start = max(1, base_c_idx + 1)

            for j in range(insert_start, len(base)):
                candidate = base[:j] + seg + base[j:]
                if not is_route_feasible(candidate, time_mtx, customers, depot):
                    continue
                d = route_distance(candidate, dist_mtx)
                if d + 1e-9 < best_dist:
                    best_dist = d
                    best_path = candidate
                    improved = True

    if improved:
        route.path = best_path
        route = update_route_metrics(route, dist_mtx, time_mtx, customers)
    return route, improved


def exchange_improve(route: Route, dist_mtx: np.ndarray,
                     time_mtx: np.ndarray,
                     customers: Dict[int, Customer],
                     depot: Depot,
                     current_time: float = 0.0) -> Tuple[Route, bool]:
    """
    Exchange: tukar posisi dua node uncommitted dalam satu rute.
    Hanya menukar node yang belum dikunjungi kendaraan.
    """
    path = route.path
    best_path = path[:]
    best_dist = route.total_distance
    improved = False

    c_idx = get_committed_index(path, time_mtx, customers, depot.tw_open, current_time)
    start_pos = max(1, c_idx + 1)

    for i in range(start_pos, len(path) - 1):
        for j in range(i + 1, len(path) - 1):
            candidate = path[:]
            candidate[i], candidate[j] = candidate[j], candidate[i]
            if not is_route_feasible(candidate, time_mtx, customers, depot):
                continue
            d = route_distance(candidate, dist_mtx)
            if d + 1e-9 < best_dist:
                best_dist = d
                best_path = candidate
                improved = True

    if improved:
        route.path = best_path
        route = update_route_metrics(route, dist_mtx, time_mtx, customers)
    return route, improved


# ─────────────────────────────────────────────────────────────
# PENCARIAN LOKAL — PERBAIKAN INTER-RUTE (ANTAR DUA RUTE)
# ─────────────────────────────────────────────────────────────

def relocate_inter(routes: List[Route], dist_mtx: np.ndarray,
                   time_mtx: np.ndarray,
                   customers: Dict[int, Customer],
                   depot: Depot,
                   current_time: float = 0.0) -> Tuple[List[Route], bool]:
    """
    Relocate: pindahkan satu node uncommitted dari satu rute ke rute lain.
    Berguna saat satu rute terlalu padat dan rute lain masih punya sisa kapasitas.
    """
    best_saving = 0.0
    best_move = None

    for r1_idx in range(len(routes)):
        for r2_idx in range(len(routes)):
            if r1_idx == r2_idx:
                continue
            r1, r2 = routes[r1_idx], routes[r2_idx]
            old_cost = r1.total_distance + r2.total_distance

            c_idx1 = get_committed_index(
                r1.path, time_mtx, customers, depot.tw_open, current_time
            )
            start_pos1 = max(1, c_idx1 + 1)

            for i in range(start_pos1, len(r1.path) - 1):
                node = r1.path[i]
                new_r1_path = r1.path[:i] + r1.path[i + 1:]

                c_idx2 = get_committed_index(
                    r2.path, time_mtx, customers, depot.tw_open, current_time
                )
                start_pos2 = max(1, c_idx2 + 1)

                for j in range(start_pos2, len(r2.path)):
                    new_r2_path = r2.path[:j] + [node] + r2.path[j:]

                    if (not is_route_feasible(new_r1_path, time_mtx, customers, depot) or
                            not is_route_feasible(new_r2_path, time_mtx, customers, depot)):
                        continue

                    new_cost = (route_distance(new_r1_path, dist_mtx) +
                                route_distance(new_r2_path, dist_mtx))
                    saving = old_cost - new_cost

                    if saving > best_saving + 1e-9:
                        best_saving = saving
                        best_move = (r1_idx, r2_idx, new_r1_path, new_r2_path)

    if best_move:
        r1i, r2i, p1, p2 = best_move
        routes[r1i].path = p1
        routes[r2i].path = p2
        routes[r1i] = update_route_metrics(routes[r1i], dist_mtx, time_mtx, customers)
        routes[r2i] = update_route_metrics(routes[r2i], dist_mtx, time_mtx, customers)
        # Buang rute yang jadi kosong setelah relokasi
        routes = [r for r in routes if not r.is_empty]
        return routes, True

    return routes, False


def swap_inter(routes: List[Route], dist_mtx: np.ndarray,
               time_mtx: np.ndarray,
               customers: Dict[int, Customer],
               depot: Depot,
               current_time: float = 0.0) -> Tuple[List[Route], bool]:
    """
    Swap(1,1): tukar satu node uncommitted antara dua rute berbeda.
    Bisa menghasilkan distribusi muatan yang lebih seimbang antar kendaraan.
    """
    best_saving = 0.0
    best_move = None

    for r1_idx in range(len(routes)):
        for r2_idx in range(r1_idx + 1, len(routes)):
            r1, r2 = routes[r1_idx], routes[r2_idx]
            old_cost = r1.total_distance + r2.total_distance

            c_idx1 = get_committed_index(
                r1.path, time_mtx, customers, depot.tw_open, current_time
            )
            start_pos1 = max(1, c_idx1 + 1)

            c_idx2 = get_committed_index(
                r2.path, time_mtx, customers, depot.tw_open, current_time
            )
            start_pos2 = max(1, c_idx2 + 1)

            for i in range(start_pos1, len(r1.path) - 1):
                for j in range(start_pos2, len(r2.path) - 1):
                    p1 = r1.path[:]
                    p2 = r2.path[:]
                    p1[i], p2[j] = p2[j], p1[i]

                    if (not is_route_feasible(p1, time_mtx, customers, depot) or
                            not is_route_feasible(p2, time_mtx, customers, depot)):
                        continue

                    new_cost = route_distance(p1, dist_mtx) + route_distance(p2, dist_mtx)
                    saving = old_cost - new_cost

                    if saving > best_saving + 1e-9:
                        best_saving = saving
                        best_move = (r1_idx, r2_idx, p1, p2)

    if best_move:
        r1i, r2i, p1, p2 = best_move
        routes[r1i].path = p1
        routes[r2i].path = p2
        routes[r1i] = update_route_metrics(routes[r1i], dist_mtx, time_mtx, customers)
        routes[r2i] = update_route_metrics(routes[r2i], dist_mtx, time_mtx, customers)
        return routes, True

    return routes, False


# ─────────────────────────────────────────────────────────────
# RVND — RANDOMIZED VARIABLE NEIGHBORHOOD DESCENT
# ─────────────────────────────────────────────────────────────

def rvnd_optimize(routes: List[Route],
                  dist_mtx: np.ndarray,
                  time_mtx: np.ndarray,
                  customers: Dict[int, Customer],
                  depot: Depot,
                  current_time: float = 0.0) -> Tuple[List[Route], List[Dict]]:
    """
    RVND: optimasi lokal dengan 5 struktur neighborhood secara acak.
    Operator intra-rute: 2-Opt, Or-Opt, Exchange.
    Operator inter-rute: Relocate, Swap(1,1).

    Mengunci node-node yang sudah dikunjungi (committed) agar tidak diubah.
    Proses berulang sampai tidak ada perbaikan lagi di semua neighborhood.
    """
    routes = copy.deepcopy(routes)
    log = []

    # Fase 1: Perbaikan intra-rute (dalam setiap rute)
    intra_ops = [
        ("2-Opt", two_opt_improve),
        ("Or-Opt", or_opt_improve),
        ("Exchange", exchange_improve),
    ]
    for r_idx in range(len(routes)):
        for name, op in intra_ops:
            routes[r_idx], imp = op(
                routes[r_idx], dist_mtx, time_mtx, customers, depot, current_time
            )
            if imp:
                log.append({
                    "operator": name, "type": "intra",
                    "route": r_idx + 1, "status": "diperbaiki"
                })

    # Fase 2: Perbaikan inter-rute (antar rute kendaraan)
    inter_ops = [
        ("Relocate", relocate_inter),
        ("Swap(1,1)", swap_inter),
    ]

    improved = True
    while improved:
        improved = False
        ops = inter_ops[:]
        random.shuffle(ops)

        for name, op in ops:
            routes, imp = op(routes, dist_mtx, time_mtx, customers, depot, current_time)
            if imp:
                log.append({"operator": name, "type": "inter", "status": "diperbaiki"})
                improved = True

                # Setelah inter-route berubah, coba optimasi ulang intra-route
                for r_idx in range(len(routes)):
                    for iname, iop in intra_ops:
                        routes[r_idx], iimp = iop(
                            routes[r_idx], dist_mtx, time_mtx,
                            customers, depot, current_time
                        )
                        if iimp:
                            log.append({
                                "operator": iname, "type": "intra",
                                "route": r_idx + 1, "status": "diperbaiki"
                            })
                break  # ulangi loop inter dari awal setelah perbaikan

    return routes, log


# ─────────────────────────────────────────────────────────────
# MESIN SIMULASI DVRPTW
# ─────────────────────────────────────────────────────────────

def run_dvrptw_simulation(
    customers: Dict[int, Customer],
    dist_mtx: np.ndarray,
    time_mtx: np.ndarray,
    depot: Depot,
    time_step: float = 0.05,    # interval langkah simulasi (jam)
    apply_rvnd: bool = True,
) -> Dict:
    """
    Simulasi DVRPTW lengkap dengan tahapan:
    1. Bangun rute awal dari pelanggan statis menggunakan Nearest Neighbor
    2. Jalankan jam virtual (virtual clock) dari depot buka sampai depot tutup
    3. Setiap time step, periksa pelanggan dinamis yang muncul (reveal_time <= t)
    4. Sisipkan pelanggan dinamis ke posisi terbaik setelah node committed
       (non-preemption — cheapest insertion)
    5. Jalankan RVND untuk optimasi lokal pada bagian rute yang belum ditempuh

    Evaluasi performa:
    - Bandingkan Solusi Dinamis (online/real-time) vs Solusi Statis Ideal (offline)
    - Dynamic Overhead Gap (%) = seberapa besar tambahan jarak akibat ketidakpastian
    """
    # Pisahkan pelanggan berdasarkan tipe: statis (diketahui sejak awal) vs dinamis
    static_ids = [c.id for c in customers.values() if not c.is_dynamic]
    dynamic_pool = {c.id: c for c in customers.values() if c.is_dynamic}

    # ──────────────────────────────────────────────
    # SOLUSI STATIS IDEAL (OFFLINE BENCHMARK)
    # Asumsikan SEMUA pelanggan sudah diketahui sejak jam buka depot
    # ──────────────────────────────────────────────
    all_cust_ids = list(customers.keys())
    ideal_static_routes = nearest_neighbor(
        all_cust_ids, dist_mtx, time_mtx, customers, depot
    )
    if apply_rvnd and ideal_static_routes:
        ideal_static_routes, _ = rvnd_optimize(
            ideal_static_routes, dist_mtx, time_mtx, customers,
            depot, current_time=depot.tw_open
        )
    ideal_static_dist = total_distance(ideal_static_routes, dist_mtx)

    # ──────────────────────────────────────────────
    # FASE 1: SOLUSI AWAL DARI PELANGGAN STATIS
    # Menggunakan Nearest Neighbor pada t = depot.tw_open
    # ──────────────────────────────────────────────
    initial_routes = nearest_neighbor(
        static_ids, dist_mtx, time_mtx, customers, depot
    )

    if apply_rvnd and initial_routes:
        initial_routes, init_log = rvnd_optimize(
            initial_routes, dist_mtx, time_mtx, customers,
            depot, current_time=depot.tw_open
        )
    else:
        init_log = []

    # Catat event pertama: rute awal terbentuk
    events = []
    events.append({
        "time": depot.tw_open,
        "event": "SOLUSI_AWAL",
        "detail": f"Rute awal terbentuk: {len(initial_routes)} rute, "
                  f"{len(static_ids)} pelanggan statis",
        "routes": copy.deepcopy(initial_routes),
        "total_distance": total_distance(initial_routes, dist_mtx),
    })

    current_routes = copy.deepcopy(initial_routes)
    revealed_dynamic = set()

    # ──────────────────────────────────────────────
    # FASE 2: SIMULASI JAM VIRTUAL (TIME-STEPPING)
    # Cek pelanggan dinamis yang muncul setiap time step
    # ──────────────────────────────────────────────
    t = depot.tw_open
    while t <= depot.tw_close and (len(revealed_dynamic) < len(dynamic_pool)):
        newly_revealed = []
        for cid, cust in list(dynamic_pool.items()):
            if cust.reveal_time <= t and cid not in revealed_dynamic:
                newly_revealed.append(cid)
                revealed_dynamic.add(cid)

        # Sisipkan setiap pelanggan dinamis baru menggunakan Cheapest Insertion
        for cid in newly_revealed:
            current_routes = cheapest_insertion(
                cid, current_routes, dist_mtx, time_mtx,
                customers, depot, current_time=t
            )

            events.append({
                "time": round(t, 4),
                "event": "PENYISIPAN_DINAMIS",
                "detail": (
                    f"Pelanggan {cid} muncul (Reveal Time "
                    f"{customers[cid].reveal_time:.2f}) & disisipkan "
                    f"setelah node committed"
                ),
                "customer_id": cid,
                "routes": copy.deepcopy(current_routes),
                "total_distance": total_distance(current_routes, dist_mtx),
            })

            # Optimasi lokal setelah penyisipan (hanya bagian rute yang belum ditempuh)
            if apply_rvnd:
                current_routes, _ = rvnd_optimize(
                    current_routes, dist_mtx, time_mtx, customers,
                    depot, current_time=t
                )
                events.append({
                    "time": round(t, 4),
                    "event": "RE_OPTIMASI",
                    "detail": "Optimasi lokal RVND pada sisa rute yang belum ditempuh",
                    "routes": copy.deepcopy(current_routes),
                    "total_distance": total_distance(current_routes, dist_mtx),
                })

        t += time_step

    # Tangani pelanggan dinamis yang belum sempat muncul sebelum depot tutup
    for cid, cust in dynamic_pool.items():
        if cid not in revealed_dynamic:
            current_routes = cheapest_insertion(
                cid, current_routes, dist_mtx, time_mtx,
                customers, depot, current_time=depot.tw_close
            )
            revealed_dynamic.add(cid)
            if apply_rvnd:
                current_routes, _ = rvnd_optimize(
                    current_routes, dist_mtx, time_mtx, customers,
                    depot, current_time=depot.tw_close
                )

    # ──────────────────────────────────────────────
    # FASE 3: KOMPILASI HASIL AKHIR
    # ──────────────────────────────────────────────
    final_routes = current_routes
    final_dist = total_distance(final_routes, dist_mtx)
    final_time = total_time(final_routes, time_mtx, customers)

    # Hitung Dynamic Overhead Gap: perbandingan efisiensi online vs offline
    gap_pct = (
        (final_dist - ideal_static_dist) / ideal_static_dist * 100
        if ideal_static_dist > 0 else 0
    )

    return {
        "initial_routes": initial_routes,
        "final_routes": final_routes,
        "ideal_static_routes": ideal_static_routes,
        "events": events,
        "init_log": init_log,
        "final_log": [],
        "metrics": {
            "ideal_static_distance": ideal_static_dist,
            "initial_distance": total_distance(initial_routes, dist_mtx),
            "final_distance": final_dist,
            "final_time": final_time,
            "dynamic_gap_pct": gap_pct,
            "total_routes": len(final_routes),
            "static_customers": len(static_ids),
            "dynamic_customers": len(dynamic_pool),
            "total_customers": len(customers),
        },
    }
