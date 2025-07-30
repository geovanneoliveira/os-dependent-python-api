import os
import csv
import json
import sys

def detect_environment(name):
    name = name.lower()
    if "mac" in name:
        return "mac"
    elif "linux" in name or "ubuntu" in name:
        return "linux"
    elif "windows" in name or "win" in name:
        return "windows"
    else:
        return "unknown"

def get_project_info_from_csv(csv_path):
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        lines = list(reader)
        if len(lines) < 2:
            return None, None
        second_line = lines[1]
        line_str = ','.join(second_line)
        project_name = line_str.split(",")[0].strip()
        environment = line_str.split(",")[-1].strip()
        return project_name, environment

def process_json(file_path, project, environment):
    with open(file_path, "r") as f:
        data = json.load(f)

    rows = []
    for test in data.get("tests", []):
        nodeid = test.get("nodeid")
        stages = ["setup", "call", "teardown"]

        for stage in stages:
            stage_data = test.get(stage)
            if stage_data:
                outcome = stage_data.get("outcome")
                crash = stage_data.get("crash", {})
                lineno = crash.get("lineno", test.get("lineno"))
                rows.append({
                    "project": project,
                    "test_name": nodeid,
                    "outcome": outcome,
                    "lineno": lineno,
                    "environment": environment
                })
                break

    for collector in data.get("collectors", []):
        if collector.get("outcome") == "failed":
            rows.append({
                "project": project,
                "test_name": collector.get("nodeid", "<unknown>"),
                "outcome": "collection_error",
                "lineno": None,
                "environment": environment
            })

    return rows

def main():
    if len(sys.argv) != 2:
        print(f"Uso: python {os.path.basename(__file__)} <pasta_base>")
        sys.exit(1)

    base_dir = sys.argv[1]
    output_path = os.path.join(base_dir, "final_all.csv")

    # Escreve o cabeçalho uma vez no início
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["project", "test_name", "outcome", "lineno", "environment"])
        writer.writeheader()

    for subdir in os.listdir(base_dir):
        subpath = os.path.join(base_dir, subdir)
        if not os.path.isdir(subpath):
            continue

        csv_file = None
        json_file = None

        print(f'Processando subdir: {subpath}')

        # os.walk percorre recursivamente todas as subpastas
        for root, dirs, files in os.walk(subpath):
            for file in files:
                if file.endswith(".csv") and csv_file is None:
                    csv_file = os.path.join(root, file)
                    print(f'  CSV encontrado: {csv_file}')
                elif file.endswith(".json") and json_file is None:
                    json_file = os.path.join(root, file)
                    print(f'  JSON encontrado: {json_file}')
                
                # Para quando encontrar ambos os arquivos
                if csv_file and json_file:
                    break
            
            if csv_file and json_file:
                break

        # Processar os arquivos encontrados
        # if csv_file or json_file:
        print(f'  Arquivos finais - CSV: {csv_file}, JSON: {json_file}')
        # Aqui você faria o processamento dos arquivos


        if not csv_file or not json_file:
            print(f"⚠️  Arquivos CSV ou JSON faltando em {subpath}")
            continue

        project_name, env_from_csv = get_project_info_from_csv(csv_file)
        if not project_name:
            print(f"⚠️  Não foi possível extrair informações de {csv_file}")
            continue

        environment = env_from_csv or detect_environment(csv_file)
        rows = process_json(json_file, project_name, environment)

        # Append ao CSV conforme processa cada pasta
        with open(output_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["project", "test_name", "outcome", "lineno", "environment"])
            for row in rows:
                writer.writerow(row)

        print(f"✅ Processado: {subpath} ({len(rows)} testes)")

    print(f"\n🏁 Arquivo final salvo em: {output_path}")

if __name__ == "__main__":
    main()
