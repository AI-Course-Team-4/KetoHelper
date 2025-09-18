import { useEffect } from "react";


type KakaoMapProps = {
  lat?: number;
  lng?: number;
  level?: number;
  height?: number | string;
  markers?: { lat: number; lng: number; title?: string; phone?: string }[];
  markerSize?: number; // px
  onMarkerClick?: (payload: { index: number; lat: number; lng: number; title?: string; }) => void;
  // 레스토랑 데이터로 마커를 찍고 싶을 때 사용 (lat/lng 없으면 address로 지오코딩)
  restaurants?: Array<{
    id: string;
    name: string;
    address: string;
    lat?: number;
    lng?: number;
  }>;
};


const KakaoMap: React.FC<KakaoMapProps> = ({
  lat,
  lng,
  level = 2,
  height = '100%',
  markerSize = 64,
  onMarkerClick,
  markers,
  restaurants,
}) => {
  const DEFAULT_LAT = lat;
  const DEFAULT_LNG = lng;
  useEffect(() => {
    if (!import.meta.env.VITE_KAKAO_MAP_JSKEY) {
      console.error("VITE_KAKAO_MAP_JSKEY 가 설정되지 않았습니다.");
      return;
    }


    const createdMarkers: any[] = [];
    const createdOverlays: any[] = [];


    const initMap = () => {
      if (!(window as any).kakao?.maps?.load) return;
      window.kakao.maps.load(async () => {
        const container = document.getElementById("map");
        if (!container) return;


        // 지도 옵션
        const options = {
          center: new window.kakao.maps.LatLng(lat, lng),
          level,
        };
        const map = new window.kakao.maps.Map(container, options);


        // SVG 기반 커스텀 마커 이미지, 초록 핀 + 작은 중앙 점만 흰색
        const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${markerSize}" height="${markerSize}" viewBox="0 0 24 24">
  <path fill="#4caf50" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z"/>
  <circle cx="12" cy="9.5" r="3" fill="#ffffff"/>
</svg>`;
        const dataUrl = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg);


        const imageSize = new window.kakao.maps.Size(markerSize, markerSize);


        const imageOffset = new window.kakao.maps.Point(Math.floor(markerSize / 2), markerSize);


        const markerImage = new window.kakao.maps.MarkerImage(dataUrl, imageSize, { offset: imageOffset });


        // positions 계산: restaurants → lat/lng or geocode(address), 아니면 markers prop, 아니면 단일 기본 좌표
        let positions: Array<{ lat: number; lng: number; title?: string; address?: string; }> = [];
        if (restaurants && restaurants.length > 0) {
          const hasMissing = restaurants.some(r => typeof r.lat !== 'number' || typeof r.lng !== 'number');
          if (!hasMissing) {
            positions = restaurants.map(r => ({ lat: r.lat as number, lng: r.lng as number, title: r.name, address: r.address }));
          } else if ((window as any).kakao?.maps?.services?.Geocoder) {
            const geocoder = new window.kakao.maps.services.Geocoder();
            const geocodeOne = (addr: string) =>
              new Promise<{ lat?: number; lng?: number }>((resolve) => {
                geocoder.addressSearch(addr, (result: any[], status: string) => {
                  if (status === window.kakao.maps.services.Status.OK && result[0]) {
                    resolve({ lat: parseFloat(result[0].y), lng: parseFloat(result[0].x) });
                  } else {
                    resolve({});
                  }
                });
              });


            for (const r of restaurants) {
              let coord = { lat: r.lat, lng: r.lng } as { lat?: number; lng?: number };
              if (typeof coord.lat !== 'number' || typeof coord.lng !== 'number') {
                const geo = await geocodeOne(r.address);
                coord = geo;
              }
              if (typeof coord.lat === 'number' && typeof coord.lng === 'number') {
                positions.push({ lat: coord.lat!, lng: coord.lng!, title: r.name, address: r.address });
              }
            }
          } else {
            // services 라이브러리가 없으면 좌표가 있는 것들만 표시
            positions = restaurants
              .filter(r => typeof r.lat === 'number' && typeof r.lng === 'number')
              .map(r => ({ lat: r.lat as number, lng: r.lng as number, title: r.name, address: r.address }));
          }
        } else if (Array.isArray(markers) && markers.length > 0) {
          positions = markers.map((m: { lat: number; lng: number; title?: string }) => ({ lat: m.lat, lng: m.lng, title: m.title }));
          positions = markers.map((m: { lat: number; lng: number; title?: string; }) => ({ lat: m.lat, lng: m.lng, title: m.title }));
        } else {
          if (lat === DEFAULT_LAT && lng === DEFAULT_LNG) {
            positions = [{ lat: lat as number, lng: lng as number, title: '강남역', address: '서울특별시 강남구 강남대로 지하396 (역삼동 858)' }];
          } else {
            positions = [{ lat: lat as number, lng: lng as number }];
          }
        }


        // restaurants/markers가 있으면 화면에 모두 보이도록 bounds 적용
        if (positions.length > 0 && (restaurants?.length || markers?.length)) {
          const bounds = new window.kakao.maps.LatLngBounds();
          positions.forEach(p => bounds.extend(new window.kakao.maps.LatLng(p.lat, p.lng)));
          map.setBounds(bounds);
        }


        let openedOverlay: any = null;


        // 맵 클릭 시 열린 말풍선 닫기
        window.kakao.maps.event.addListener(map, 'click', () => {
          if (openedOverlay) {
            openedOverlay.setMap(null);
            openedOverlay = null;
          }
        });


        positions.forEach((pos, index) => {
          const marker = new window.kakao.maps.Marker({
            position: new window.kakao.maps.LatLng(pos.lat, pos.lng),
            title: (pos as any).title,
            image: markerImage,
          });
          marker.setMap(map);
          createdMarkers.push(marker);


          // 항상 표시되는 레이블(식당명) 오버레이 - 마커 위로 살짝 띄움
          if ((pos as any).title) {
            const labelHtml = `
              <span
                style="
                  display: inline-block;
                  pointer-events: none;
                  white-space: nowrap;
                  padding: 2px 6px;
                  font-size: 11px;
                  font-weight: 800;
                  color: #000000;
                  text-shadow: -1px 0 white, 0 1px white, 1px 0 white, 0 -1px white;
                  transform: translate(0, -12px);
                "
              >
                ${(pos as any).title}
              </span>`;
            const labelOverlay = new window.kakao.maps.CustomOverlay({
              position: new window.kakao.maps.LatLng(pos.lat, pos.lng),
              content: labelHtml,
              yAnchor: 0,
              xAnchor: 0.5,
              zIndex: 2,
            });
            labelOverlay.setMap(map);
            createdOverlays.push(labelOverlay);
          }


          // 클릭 시 커스텀 말풍선 오버레이 표시 및 콜백 호출
          const contentHtml = `
            <div style="position:relative;pointer-events:auto;">
              <div style="
                background:#ffffff;
                border-radius:12px;
                box-shadow:0 12px 32px rgba(0,0,0,0.3);
                border:1px solid #ddd;
                white-space:nowrap;
                min-width:200px;
                overflow:hidden;
              ">
                <div style="padding:12px 14px;font-size:13px;color:#212121;">
                  <div style="font-weight:700;margin-bottom:6px;">
                    ${(pos as any).title || ''}
                  </div>
                  ${`<div style=\"color:#616161;\">${(pos as any).address}</div>`}
                </div>
              </div>
              <div style="
                position:absolute;left:50%;bottom:-7px;transform:translateX(-50%);
                width:0;height:0;border-left:10px solid transparent;border-right:10px solid transparent;border-top:10px solid #fff;
                z-index:10;
              "></div>
              <div style="
                position:absolute;left:50%;bottom:-5px;transform:translateX(-50%);
                width:0;height:0;border-left:9px solid transparent;border-right:9px solid transparent;border-top:9px solid #ffffff;
                z-index:11;
              "></div>
            </div>`;


          const overlay = new window.kakao.maps.CustomOverlay({
            position: new window.kakao.maps.LatLng(pos.lat, pos.lng),
            content: contentHtml,
            yAnchor: 1.8,
            xAnchor: 0.5,
            zIndex: 4,
          });


          window.kakao.maps.event.addListener(marker, 'click', () => {
            if (openedOverlay) {
              openedOverlay.setMap(null);
            }
            overlay.setMap(map);
            openedOverlay = overlay;


            if (onMarkerClick) {
              onMarkerClick({ index, lat: pos.lat, lng: pos.lng, title: (pos as any).title });
            }
          });
        });
      });
    };


    if ((window as any).kakao && (window as any).kakao.maps) {
      initMap();
      return;
    }


    // SDK 스크립트 로드 (지오코딩을 위해 services 라이브러리 포함)
    const id = "kakao-maps-sdk";
    let script = document.getElementById(id) as HTMLScriptElement | null;
    if (!script) {
      script = document.createElement("script");
      script.id = id;
      script.async = true;
      script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${import.meta.env.VITE_KAKAO_MAP_JSKEY}&autoload=false&libraries=services`;
      document.head.appendChild(script);
    }
    script.addEventListener("load", initMap);


    return () => {
      script?.removeEventListener("load", initMap);
      createdMarkers.forEach((m) => m.setMap(null));
      createdOverlays.forEach((o) => o.setMap(null));
    };
  }, [lat, lng, level, markers, markerSize, onMarkerClick, restaurants]);


  const resolvedHeight = typeof height === 'number' ? `${height}px` : height;


  return <div id="map" style={{ width: "100%", height: resolvedHeight }} />;
};


export default KakaoMap;