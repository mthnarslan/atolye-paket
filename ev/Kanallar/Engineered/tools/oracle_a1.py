"""Always Free only: 1 VCN + 1 A1.Flex instance (4 OCPU / 24 GB, 100 GB boot) in Frankfurt; retries across ADs on 'Out of capacity'."""
import oci, time, sys
from pathlib import Path
cfg = oci.config.from_file(); T = cfg["tenancy"]
idn, vn, cc = oci.identity.IdentityClient(cfg), oci.core.VirtualNetworkClient(cfg), oci.core.ComputeClient(cfg)
OCPU, MEM, BOOT = 4, 24, 100   # Always Free A1 cap: 4 OCPU / 24 GB total; block storage cap 200 GB total
assert OCPU <= 4 and MEM <= 24 and BOOT <= 200

def one(lst, **kw):
    return lst[0] if lst else None

vcn = one([v for v in vn.list_vcns(T).data if v.display_name == "render-vcn" and v.lifecycle_state == "AVAILABLE"])
if not vcn:
    vcn = vn.create_vcn(oci.core.models.CreateVcnDetails(compartment_id=T, cidr_blocks=["10.0.0.0/16"], display_name="render-vcn", dns_label="render")).data
    oci.wait_until(vn, vn.get_vcn(vcn.id), "lifecycle_state", "AVAILABLE")
igw = one([g for g in vn.list_internet_gateways(T, vcn_id=vcn.id).data if g.lifecycle_state == "AVAILABLE"])
if not igw:
    igw = vn.create_internet_gateway(oci.core.models.CreateInternetGatewayDetails(compartment_id=T, vcn_id=vcn.id, is_enabled=True, display_name="render-igw")).data
    oci.wait_until(vn, vn.get_internet_gateway(igw.id), "lifecycle_state", "AVAILABLE")
rt = vn.get_route_table(vcn.default_route_table_id).data
if not rt.route_rules:
    vn.update_route_table(rt.id, oci.core.models.UpdateRouteTableDetails(route_rules=[oci.core.models.RouteRule(destination="0.0.0.0/0", destination_type="CIDR_BLOCK", network_entity_id=igw.id)]))
sub = one([s for s in vn.list_subnets(T, vcn_id=vcn.id).data if s.lifecycle_state == "AVAILABLE"])
if not sub:
    sub = vn.create_subnet(oci.core.models.CreateSubnetDetails(compartment_id=T, vcn_id=vcn.id, cidr_block="10.0.0.0/24", display_name="render-sub", dns_label="sub")).data
    oci.wait_until(vn, vn.get_subnet(sub.id), "lifecycle_state", "AVAILABLE")
print("network ok", flush=True)

imgs = cc.list_images(T, operating_system="Canonical Ubuntu", shape="VM.Standard.A1.Flex", sort_by="TIMECREATED").data
img = next(i for i in imgs if "Minimal" not in i.display_name and "aarch64" in i.display_name)
print("image", img.display_name, flush=True)
key = Path.home().joinpath(".ssh/oracle_a1.pub").read_text().strip()
ads = [a.name for a in idn.list_availability_domains(T).data]
existing = [i for i in cc.list_instances(T).data if i.display_name == "render-a1" and i.lifecycle_state not in ("TERMINATED", "TERMINATING")]
inst = existing[0] if existing else None
n = 0
while not inst:
    for ad in ads:
        n += 1
        try:
            inst = cc.launch_instance(oci.core.models.LaunchInstanceDetails(
                compartment_id=T, availability_domain=ad, display_name="render-a1", shape="VM.Standard.A1.Flex",
                shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(ocpus=OCPU, memory_in_gbs=MEM),
                source_details=oci.core.models.InstanceSourceViaImageDetails(image_id=img.id, boot_volume_size_in_gbs=BOOT),
                create_vnic_details=oci.core.models.CreateVnicDetails(subnet_id=sub.id, assign_public_ip=True),
                metadata={"ssh_authorized_keys": key})).data
            print("launched in", ad, flush=True); break
        except oci.exceptions.ServiceError as e:
            print(time.strftime("%H:%M:%S"), n, ad[-4:], e.status, e.message[:70], flush=True)
            if e.status not in (500, 429) and "capacity" not in e.message.lower():
                sys.exit(1)
            time.sleep(5)
    else:
        time.sleep(30)
oci.wait_until(cc, cc.get_instance(inst.id), "lifecycle_state", "RUNNING", max_wait_seconds=900)
va = cc.list_vnic_attachments(T, instance_id=inst.id).data[0]
ip = vn.get_vnic(va.vnic_id).data.public_ip
print("RUNNING", ip, flush=True)
Path.home().joinpath(".oci/a1_ip").write_text(ip)
