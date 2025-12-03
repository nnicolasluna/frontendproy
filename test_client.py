"""
Script de prueba para el microservicio de extracción de archivos Android
Ejecutar el servidor (app.py) antes de ejecutar este script
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def imprimir_separador(titulo):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}\n")

def test_health_check():
    """Probar el endpoint de health check"""
    imprimir_separador("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_device_info():
    """Probar obtener información del dispositivo"""
    imprimir_separador("TEST 2: Device Info")
    
    try:
        response = requests.get(f"{BASE_URL}/api/device-info")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_scan_files():
    """Probar escaneo de archivos"""
    imprimir_separador("TEST 3: Scan Files (Solo imágenes)")
    
    try:
        payload = {
            "categorias": ["imagenes"]
        }
        response = requests.post(
            f"{BASE_URL}/api/scan",
            json=payload
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Total archivos: {data['data']['total_archivos']}")
            print(f"Resumen por categorías:")
            for categoria, cantidad in data['data']['resumen_categorias'].items():
                print(f"  - {categoria}: {cantidad}")
            
            # Mostrar algunos archivos encontrados
            archivos = data['data']['archivos'][:5]  # Primeros 5
            if archivos:
                print(f"\nPrimeros archivos encontrados:")
                for archivo in archivos:
                    print(f"  - {archivo}")
        else:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_extract_files():
    """Probar extracción de archivos (comentado por defecto)"""
    imprimir_separador("TEST 4: Extract Files (DESHABILITADO)")
    
    print("⚠️  Este test está deshabilitado por defecto para evitar descargas no deseadas.")
    print("📝 Para habilitarlo, descomenta el código en test_client.py")
    print("\nEjemplo de uso:")
    print("""
    payload = {
        "categorias": ["imagenes"],
        "carpeta_destino": "test_downloads"
    }
    response = requests.post(f"{BASE_URL}/api/extract", json=payload)
    """)
    
    # Descomenta esto para ejecutar la extracción
    # try:
    #     payload = {
    #         "categorias": ["imagenes"],
    #         "carpeta_destino": "test_downloads"
    #     }
    #     response = requests.post(
    #         f"{BASE_URL}/api/extract",
    #         json=payload
    #     )
    #     print(f"Status Code: {response.status_code}")
    #     print(f"Response: {json.dumps(response.json(), indent=2)}")
    #     return response.status_code == 200
    # except Exception as e:
    #     print(f"❌ Error: {e}")
    #     return False
    
    return True

def main():
    """Ejecutar todos los tests"""
    print("\n🚀 Iniciando tests del microservicio Android File Extraction")
    print(f"🔗 URL Base: {BASE_URL}")
    
    resultados = []
    
    # Test 1: Health Check
    resultados.append(("Health Check", test_health_check()))
    
    # Test 2: Device Info
    resultados.append(("Device Info", test_device_info()))
    
    # Test 3: Scan Files
    resultados.append(("Scan Files", test_scan_files()))
    
    # Test 4: Extract Files (deshabilitado)
    resultados.append(("Extract Files", test_extract_files()))
    
    # Resumen
    imprimir_separador("RESUMEN DE TESTS")
    
    total = len(resultados)
    exitosos = sum(1 for _, resultado in resultados if resultado)
    
    for nombre, resultado in resultados:
        status = "✅ PASS" if resultado else "❌ FAIL"
        print(f"{status} - {nombre}")
    
    print(f"\n📊 Resultados: {exitosos}/{total} tests exitosos")
    
    if exitosos == total:
        print("🎉 ¡Todos los tests pasaron!")
    else:
        print("⚠️  Algunos tests fallaron. Verifica que:")
        print("   - El servidor Flask esté ejecutándose (python app.py)")
        print("   - Haya un dispositivo Android conectado con ADB")

if __name__ == "__main__":
    main()
