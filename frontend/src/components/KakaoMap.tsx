import { useEffect } from "react";

type KakaoMapProps = {
  lat?: number;
  lng?: number;
  level?: number;
  height?: number | string;
};

const KakaoMap: React.FC<KakaoMapProps> = ({
  lat = 37.5665,
  lng = 126.9780,
  level = 3,
}) => {
  useEffect(() => {
    if (!import.meta.env.VITE_KAKAO_MAP_JSKEY) {
      console.error("VITE_KAKAO_JS_KEY가 설정되지 않았습니다.");
      return;
    }

    const initMap = () => {
      if (!(window as any).kakao?.maps?.load) return;
      // @ts-ignore
      window.kakao.maps.load(() => {
        const container = document.getElementById("map");
        if (!container) return;

        // 지도 옵션
        const options = {
          center: new window.kakao.maps.LatLng(lat, lng),
          level,
        };
        const map = new window.kakao.maps.Map(container, options);

        // 마커
        const marker = new window.kakao.maps.Marker({
          position: new window.kakao.maps.LatLng(lat, lng),
        });
        marker.setMap(map);
      });
    };

    // 이미 로드된 경우 바로 초기화
    if ((window as any).kakao && (window as any).kakao.maps) {
      initMap();
      return;
    }

    // SDK 스크립트 로드
    const id = "kakao-maps-sdk";
    let script = document.getElementById(id) as HTMLScriptElement | null;
    if (!script) {
      script = document.createElement("script");
      script.id = id;
      script.async = true;
      script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${import.meta.env.VITE_KAKAO_MAP_JSKEY}&autoload=false`;
      document.head.appendChild(script);
    }
    script.addEventListener("load", initMap);

    return () => {
      script?.removeEventListener("load", initMap);
    };
  }, [lat, lng, level]);

  return <div id="map" style={{ width: "100%", height: "100%" }} />;
};

export default KakaoMap;