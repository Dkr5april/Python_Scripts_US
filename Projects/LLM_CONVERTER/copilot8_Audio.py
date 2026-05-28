import pyaudiowpatch as pyaudio

def find_my_headset_specs():
    p = pyaudio.PyAudio()
    try:
        # 1. Get the primary WASAPI output (where your YouTube sound goes)
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_out = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        
        print("--- ACTIVE HARDWARE REPORT ---")
        print(f"Target Output: {default_out['name']}")
        
        # 2. Find the loopback (the 'ears') for that specific headset
        loopback_device = None
        for dev in p.get_loopback_device_info_generator():
            if default_out["name"] in dev["name"]:
                loopback_device = dev
                break
        
        if loopback_device:
            print(f"Device Index: {loopback_device['index']}")
            print(f"Native Sample Rate: {int(loopback_device['defaultSampleRate'])} Hz")
            print(f"Hardware Channels: {loopback_device['maxInputChannels']}")
            print("------------------------------")
            print("\n✅ USE THESE VALUES IN YOUR MAIN SCRIPT:")
            print(f"Rate: {int(loopback_device['defaultSampleRate'])}")
            print(f"Channels: {loopback_device['maxInputChannels']}")
        else:
            print("❌ Headset Loopback not found. Make sure it's set as 'Default' in Windows.")

    finally:
        p.terminate()

if __name__ == "__main__":
    find_my_headset_specs()